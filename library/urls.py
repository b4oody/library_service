from django.urls import path, include

from library.views import index, catalog, profile, book_page, sign_up

urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("registration/", sign_up, name="registration"),

    path("catalog/", catalog, name="catalog"),

]

app_name = "library"
