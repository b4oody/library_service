from django.contrib.auth import login
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect

from library.form import RegistrationForm, BookFilterForm
from library.models import Book


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
    context = {
        "book_pk": Book.objects.get(pk=pk),
    }
    return render(
        request,
        "catalog/book-page.html",
        context=context
    )
