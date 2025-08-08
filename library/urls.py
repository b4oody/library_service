from django.urls import path, include

from library.views import (
    index_page_view,
    catalog_page_view,
    profile_page_view,
    sign_up_view,
    book_page_view,
    BookCreateAdminView,
    BookUpdateAdminView,
    BookDeleteAdminView,
    GenreCreateAdminView,
    AuthorCreateAdminView,
    add_liked_book,
    delete_liked_book_view,
    PurchaseCreateView,
    AddToCartView,
)

urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("registration/", sign_up_view, name="registration"),
    path("", index_page_view, name="index_page_view"),
    path("profile/", profile_page_view, name="profile"),
    path("catalog/", catalog_page_view, name="catalog_page_view"),
    path("book_page/<int:pk>/", book_page_view, name="book_page_view"),
    path("book_create/", BookCreateAdminView.as_view(), name="book_create_view"),
    path("book_update/<int:pk>/", BookUpdateAdminView.as_view(), name="book_update_view"),
    path("book_delete/<int:pk>/", BookDeleteAdminView.as_view(), name="book_delete_view"),
    path("genre_create/", GenreCreateAdminView.as_view(), name="genre_create_view"),
    path("author_create/", AuthorCreateAdminView.as_view(), name="author_create_view"),
    path("add_liked_book/<int:pk>/", add_liked_book, name="add_liked_book"),
    path("delete_liked_book/<int:pk>/", delete_liked_book_view, name="delete_liked_book_view"),
    path("create_purchase/", PurchaseCreateView.as_view(), name="purchase_create_view"),
    path("add_to_cart_item/<int:book_id>/", AddToCartView.as_view(), name="add_to_cart_item"),

]

app_name = "library"
