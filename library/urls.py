from django.urls import path, include

from library.views import (
    index_page_view,
    catalog_page_view,
    profile,
    sign_up_view,
    book_page_view,
    BookCreateAdminView,
    BookUpdateAdminView,
)

urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("registration/", sign_up_view, name="registration"),
    path("", index_page_view, name="index_page_view"),
    path("profile/", profile, name="profile"),
    path("catalog/", catalog_page_view, name="catalog_page_view"),
    path("book_page/<int:pk>/", book_page_view, name="book_page_view"),
    path("book_create/", BookCreateAdminView.as_view(), name="book_create_view"),
    path("book_update/<int:pk>/", BookUpdateAdminView.as_view(), name="book_update_view"),

]

app_name = "library"
