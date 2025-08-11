from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic, View
from django.views.generic import FormView, UpdateView

from library.form import RegistrationForm, BookFilterForm, PurchaseForm
from library.models import Book, Purchase, LikedBook, Genre, Author, PurchaseItem


def sign_up_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            login(request, user)
            return redirect("library:catalog_page_view")
    else:
        form = RegistrationForm()
    return render(request, "registration/registration.html", {"form": form})


@login_required
def profile_page_view(request: HttpRequest) -> HttpResponse:
    book_purchases = Purchase.objects.filter(user=request.user)
    books_liked = LikedBook.objects.filter(user=request.user)

    return render(
        request,
        "profile/profile.html",
        context={"book_purchases": book_purchases, "book_liked": books_liked},
    )


def index_page_view(request: HttpRequest) -> HttpResponse:
    return render(request, "index/index.html")


def catalog_page_view(request: HttpRequest) -> HttpResponse:
    books = Book.objects.prefetch_related("author", "genres")
    form_filter = BookFilterForm(request.GET)
    if form_filter.is_valid():
        books = apply_filters_and_sort(books, form_filter.cleaned_data)

    per_page = get_per_page(request)
    paginator = Paginator(books, per_page)
    page_obj = get_paginated_page(request, paginator)

    context = {
        "books": page_obj,
        "page_obj": page_obj,
        "form_filter": form_filter,
        "selected_per_page": per_page,
    }
    return render(request, "catalog/catalog.html", context=context)


def apply_filters_and_sort(books, cleaned_data):
    genre = cleaned_data.get("genre")
    author = cleaned_data.get("author")
    query = cleaned_data.get("query")
    not_in_stock = cleaned_data.get("not_in_stock")
    in_stock = cleaned_data.get("in_stock")
    price_min = cleaned_data.get("price_min")
    price_max = cleaned_data.get("price_max")
    order_by_year = cleaned_data.get("order_by_year")
    order_by_title = cleaned_data.get("order_by_title")
    order_by_price = cleaned_data.get("order_by_price")

    if genre:
        books = books.filter(genres=genre)
    if author:
        books = books.filter(author=author)
    if query:
        books = books.filter(Q(title__icontains=query))
    if in_stock:
        books = books.filter(quantity__gt=0)
    if not_in_stock:
        books = books.filter(quantity=0)
    if price_min:
        books = books.filter(price__gte=price_min)
    if price_max:
        books = books.filter(price__lte=price_max)

    if order_by_title:
        books = books.order_by(order_by_title)
    if order_by_year:
        books = books.order_by(order_by_year)
    if order_by_price:
        books = books.order_by(order_by_price)

    return books


def get_per_page(request):
    per_page_param = request.GET.get("per_page", 20)
    try:
        per_page = int(per_page_param)
        if 0 < per_page <= 100:
            return per_page
        return 20
    except (ValueError, TypeError):
        return 20


def get_paginated_page(request, paginator):
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    return page_obj


def book_page_view(request: HttpRequest, pk: int) -> HttpResponse:
    is_liked_book_by_user = False
    if request.user.is_authenticated:
        is_liked_book_by_user = LikedBook.objects.filter(user=request.user, book=pk)

    context = {
        "book_pk": Book.objects.get(pk=pk),
        "is_liked_book_by_user": is_liked_book_by_user,
    }
    return render(request, "catalog/book-page.html", context=context)


class CreateAdminView(generic.CreateView):
    model = Genre
    template_name = "catalog/create_update_form.html"
    fields = "__all__"
    success_url = reverse_lazy("library:catalog_page_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_update_form"] = context.pop("form")
        return context


class BookCreateAdminView(CreateAdminView):
    model = Book

    def get_success_url(self):
        return reverse_lazy("library:book_page_view", kwargs={"pk": self.object.pk})


class BookUpdateAdminView(generic.UpdateView):
    model = Book
    template_name = "catalog/create_update_form.html"
    fields = "__all__"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_update_form"] = context.pop("form")
        return context

    def get_success_url(self):
        return reverse_lazy("library:book_page_view", kwargs={"pk": self.object.pk})


class BookDeleteAdminView(generic.DeleteView):
    model = Book
    template_name = "catalog/delete_book_form.html"
    success_url = reverse_lazy("library:catalog_page_view")


class GenreCreateAdminView(CreateAdminView):
    model = Genre


class AuthorCreateAdminView(CreateAdminView):
    model = Author


@login_required
def add_liked_book(request: HttpRequest, pk: int) -> HttpResponse:
    book = Book.objects.get(pk=pk)
    liked_book = LikedBook.objects.create(user=request.user, book=book)
    liked_book.save()
    return redirect("library:book_page_view", pk=pk)


@login_required
def delete_liked_book_view(request: HttpRequest, pk: int) -> HttpResponse:
    book = Book.objects.get(pk=pk)
    liked_book = LikedBook.objects.get(user=request.user, book=book)
    liked_book.delete()
    return redirect("library:book_page_view", pk=pk)


class PurchaseCreateView(LoginRequiredMixin, generic.CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = "catalog/create_purchase_form.html"
    success_url = reverse_lazy("library:catalog_page_view")

    def form_valid(self, form):
        books = form.cleaned_data["books"]
        instance = form.save(commit=False)
        total_amount = 0
        for book in books:
            total_amount += book.price
        instance.user = self.request.user
        instance.total_amount = total_amount
        instance.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_update_form"] = context.pop("form")
        return context


class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        if not book.is_stock():
            messages.error(request, "На жаль, цієї книги немає в наявності.")
            return redirect(
                request.META.get("HTTP_REFERER", "library:catalog_page_view")
            )
        cart, created = Purchase.objects.get_or_create(
            user=request.user,
            payment_status="pending"
        )
        cart_item, item_created = PurchaseItem.objects.get_or_create(
            purchase=cart, book=book, defaults={"price": 0}
        )

        if not item_created:
            cart_item.quantity += 1
            cart_item.save()
        total_amount = sum(
            item.book.price * item.quantity
            for item in cart.purchaseitem_set.all()
        )
        cart.total_amount = total_amount
        cart.save()
        return redirect(request.META.get("HTTP_REFERER", "library:catalog_page_view"))


def checkout_page_view(request) -> HttpResponse:
    customer = request.user
    try:
        order = Purchase.objects.get(user=customer)
    except Purchase.DoesNotExist:
        return redirect("library:catalog_page_view")
    cart_items = PurchaseItem.objects.filter(purchase=order)
    context = {
        "order": order,
        "cart_items": cart_items,
    }
    return render(request, "catalog/checkout.html", context=context)


def delete_book_from_order(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart, created = Purchase.objects.get_or_create(
        user=request.user,
        payment_status="pending"
    )
    cart_item, item_created = PurchaseItem.objects.get_or_create(
        purchase=cart, book=book,
    )
    cart_item.delete()
    total_amount = sum(
        item.book.price * item.quantity
        for item in cart.purchaseitem_set.all()
    )
    cart.total_amount = total_amount
    cart.save()
    return redirect(request.META.get("HTTP_REFERER", "library:catalog_page_view"))


def update_cart(request):
    if request.method == "POST":
        order = get_object_or_404(Purchase, user=request.user, payment_status="pending")
        total_amount = 0
        for item in order.purchaseitem_set.all():
            qty = request.POST.get(f"quantity_{item.book.pk}")
            if qty and qty.isdigit():
                item.quantity = int(qty)
                item.save()
                total_amount += item.book.price * item.quantity

        order.total_amount = total_amount
        order.save()
        return redirect('library:checkout_page_view')

class CheckoutFormView(LoginRequiredMixin, FormView):
    model = Purchase
    fields = ["first_name", "last_name", "email"]
    success_url = reverse_lazy("library:catalog")

    def form_valid(self, form):
        order = Purchase.objects.get(user=self.request.user, status="pending")

        order.first_name = self.request.POST.get("first_name", "")
        order.last_name = self.request.POST.get("last_name", "")
        order.email = self.request.POST.get("email", "")
        order.status = "completed"
        order.save()

        messages.success(self.request, "Ваше замовлення успішно оформлено!")

        return redirect(self.success_url)


class CheckoutView(LoginRequiredMixin, UpdateView):
    model = Purchase
    fields = ["first_name", "last_name", "email"]
    template_name = "catalog/checkout.html"
    success_url = reverse_lazy("library:catalog_page_view")
    context_object_name = "order"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        cart_items = PurchaseItem.objects.filter(
            purchase=self.object,
        )

        for item in cart_items:
            if item.quantity > item.book.quantity:
                messages.error(
                    request,
                    f"На жаль, книги «{item.book.title}» недостатньо на складі. "
                    f"Доступно лише {item.book.quantity} шт."
                )
                return redirect("library:checkout_page_view")
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        try:
            order = Purchase.objects.get(user=self.request.user, payment_status="pending")
            return order
        except Purchase.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object():
            messages.warning(request, "Ваш кошик порожній. Неможливо оформити замовлення.")
            return redirect("library:catalog_page_view")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context["cart_items"] = PurchaseItem.objects.filter(
                purchase=self.object,

            )
        context["form_order"] = context.pop("form")
        return context

    def form_valid(self, form):
        order = self.object
        cart_items = PurchaseItem.objects.filter(purchase=order)

        try:
            with transaction.atomic():
                order = form.save(commit=False)
                order.payment_status = "completed"
                order.save()

                for item in cart_items:
                    book_to_update = Book.objects.select_for_update().get(pk=item.book.pk)

                    if item.quantity > book_to_update.quantity:
                        raise Exception(f"Недостатньо «{book_to_update.title}» на складі.")
                    book_to_update.quantity -= item.quantity
                    book_to_update.save()

        except Exception as e:
            messages.error(self.request, f"Виникла помилка при оформленні замовлення: {e}")
            return redirect("library:checkout_page_view")

        messages.success(self.request, "Ваше замовлення успішно оформлено!")
        return redirect(self.get_success_url())