from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
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
    books = Book.objects.all()
    form_filter = BookFilterForm(request.GET)
    if form_filter.is_valid():
        genre = form_filter.cleaned_data["genre"]
        author = form_filter.cleaned_data["author"]
        query = form_filter.cleaned_data["query"]

        if genre:
            books = books.filter(genres=genre)

        if author:
            books = books.filter(author=author)

        if query:
            books = books.filter(
                Q(title__icontains=query)
            )

    context = {
        "books": books,
        "form_filter": form_filter
    }
    return render(
        request,
        "catalog/catalog.html",
        context=context
    )


def book_page_view(request: HttpRequest, pk: int) -> HttpResponse:
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


def add_liked_book(request: HttpRequest, pk: int) -> HttpResponse:
    book = Book.objects.get(pk=pk)
    liked_book = LikedBook.objects.create(user=request.user, book=book)
    liked_book.save()
    return redirect("library:book_page_view", pk=pk)


def delete_liked_book_view(request: HttpRequest, pk: int) -> HttpResponse:
    book = Book.objects.get(pk=pk)
    liked_book = LikedBook.objects.get(user=request.user, book=book)
    liked_book.delete()
    return redirect("library:book_page_view", pk=pk)
