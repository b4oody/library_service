import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
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
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    class Meta:
        ordering = ["last_name", "first_name"]
        unique_together = ("first_name", "last_name")

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    genre_name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["genre_name"]

    def __str__(self):
        return self.genre_name


def upload_to_uuid(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    folder = "photos/"

    return os.path.join(folder, filename)

def validate_photo_size(value):
    MAX_UPLOAD_SIZE = 1 * 1024 * 1024
    if value.size > MAX_UPLOAD_SIZE:
        raise ValidationError("Файл занадто великий. Максимальний розмір — 1 MB.")

class Book(models.Model):
    title_validator = RegexValidator(
        regex=r"^[a-zA-Zа-яА-ЯёЁ0-9']+$", message="Поле може містити лише букви, цифри"
    )

    title = models.CharField(
        max_length=100,
        validators=[title_validator],
    )
    author = models.ManyToManyField(Author, related_name="books")
    genres = models.ManyToManyField(
        Genre,
        related_name="books",
    )
    publication_year = models.DateField()
    description = models.TextField()
    quantity = models.PositiveIntegerField(
        default=1,
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    cover_image_url = models.ImageField(
        upload_to=upload_to_uuid,
        blank=True,
        null=True,
        validators=[validate_photo_size],
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        authors_list = [author.full_name() for author in self.author.all()]
        return f"{self.title}: ({', '.join(authors_list)})"

    def is_stock(self):
        return self.quantity > 0


class Purchase(models.Model):
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchases",
    )
    books = models.ManyToManyField(
        Book,
        related_name="purchases",
    )
    purchase_date = models.DateTimeField(
        auto_now_add=True,
    )
    total_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        default=0,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentReservation.choices,
        default="pending",
    )

    class Meta:
        ordering = ["-purchase_date"]

    def __str__(self):
        books = [book.title for book in self.books.all()]
        return f"Purchase {", ".join(books)} by {self.user}"


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


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.purchase} {self.book} {self.quantity} {self.price}"

    def get_total_price(self):
        return self.quantity * self.price
