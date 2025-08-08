from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

from library.form import RegistrationForm, BookFilterForm
from library.models import Book, Purchase, LikedBook, Genre, Author


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
    return render(
        request,
        "registration/registration.html",
        {"form": form}
    )


@login_required
def profile_page_view(request: HttpRequest) -> HttpResponse:
    book_purchases = Purchase.objects.filter(user=request.user)
    books_liked = LikedBook.objects.filter(user=request.user)

    return render(
        request,
        "profile/profile.html",
        context={
            "book_purchases": book_purchases,
            "book_liked": books_liked
        }
    )


def index_page_view(request: HttpRequest) -> HttpResponse:
    return render(request, "index/index.html")


def catalog_page_view(request: HttpRequest) -> HttpResponse:
    books = Book.objects.prefetch_related("author", "genres")
    form_filter = BookFilterForm(request.GET)
    if form_filter.is_valid():
        genre = form_filter.cleaned_data["genre"]
        author = form_filter.cleaned_data["author"]
        query = form_filter.cleaned_data["query"]
        not_in_stock = form_filter.cleaned_data.get('not_in_stock')
        in_stock = form_filter.cleaned_data.get('in_stock')
        price_min = form_filter.cleaned_data.get('price_min')
        price_max = form_filter.cleaned_data.get('price_max')
        order_by_year = form_filter.cleaned_data.get('order_by_year')
        order_by_title = form_filter.cleaned_data.get('order_by_title')

        if genre:
            books = books.filter(genres=genre)

        if author:
            books = books.filter(author=author)

        if query:
            books = books.filter(
                Q(title__icontains=query)
            )
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

    per_page_param = request.GET.get('per_page', 20)
    try:
        per_page = int(per_page_param)
        if per_page > 100:
            per_page = 100
        if per_page <= 0:
            per_page = 20

    except (ValueError, TypeError):
        per_page = 20

    paginator = Paginator(books, per_page)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)


    context = {
        "books": page_obj,
        "page_obj": page_obj,
        "form_filter": form_filter,
        'selected_per_page': per_page,
    }
    return render(
        request,
        "catalog/catalog.html",
        context=context
    )


def book_page_view(request: HttpRequest, pk: int) -> HttpResponse:
    is_liked_book_by_user = False
    if request.user.is_authenticated:
        is_liked_book_by_user = LikedBook.objects.filter(user=request.user, book=pk)

    context = {
        "book_pk": Book.objects.get(pk=pk),
        "is_liked_book_by_user": is_liked_book_by_user
    }
    return render(
        request,
        "catalog/book-page.html",
        context=context
    )


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
        cart, created = Purchase.objects.get_or_create(
            user=request.user,
        )
        cart_item, item_created = PurchaseItem.objects.get_or_create(
            purchase=cart,
            book=book,
            defaults={"price": book.price}
        )

        if not item_created:
            cart_item.quantity += 1
            cart_item.save()
        return redirect(request.META.get("HTTP_REFERER", "library:catalog_page_view"))
