import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from config import settings


class PaymentReservation(models.TextChoices):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(AbstractUser):
    pass


class Author(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)

    class Meta:
        ordering = ["last_name", "first_name"]
        unique_together = ("first_name", "last_name")

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    genre_name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["genre_name"]

    def __str__(self):
        return self.genre_name


def upload_to_uuid(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    folder = "photos/"

    return os.path.join(folder, filename)


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ManyToManyField(
        Author,
        related_name="books"
    )
    genres = models.ManyToManyField(Genre, related_name="books", )
    publication_year = models.DateField()
    description = models.TextField()
    quantity = models.PositiveIntegerField(default=1, )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    cover_image_url = models.ImageField(
        upload_to=upload_to_uuid,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        authors_list = [author.full_name() for author in self.author.all()]
        return f"{self.title}: ({', '.join(authors_list)})"

    def is_stock(self):
        return self.quantity > 0


class Purchase(models.Model):
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchases",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="purchases",
    )
    purchase_date = models.DateTimeField(auto_now_add=True, )
    total_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentReservation.choices,
        default="pending",
    )

    class Meta:
        ordering = ["-purchase_date"]

    def __str__(self):
        return f"Purchase {self.book.title} by {self.user}"


class LikedBook(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="liked_books",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="liked_by_users",
    )
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")
        ordering = ["-added_date"]

    def __str__(self):
        return f"{self.user} liked {self.book.title}"
