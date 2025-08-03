from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from library.models import Author, Genre, Book, LikedBook, Purchase
from library.views import PurchaseCreateView

User = get_user_model()


class TestSignUpView(TestCase):
    def setUp(self):
        self.client = Client()
        self.registration_url = reverse("library:registration")

    def test_registration_page_renders_successfully(self):
        response = self.client.get(self.registration_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/registration.html")

    def test_registration_with_valid_data_creates_user(self):
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
        }

        response = self.client.post(self.registration_url, form_data, follow=True)

        self.assertEqual(User.objects.count(), 1)

        user = User.objects.get(username="testuser")
        self.assertEqual(user.email, "test@example.com")

        self.assertFalse(user.check_password("wrongpassword"))
        self.assertTrue(user.check_password("strongpassword123"))

        self.assertRedirects(response, reverse("library:catalog_page_view"))

    def test_registration_with_invalid_data_does_not_create_user(self):
        form_data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password1": "password",
            "password2": "different_password",
        }

        response = self.client.post(self.registration_url, form_data)

        self.assertEqual(User.objects.count(), 0)

        self.assertIn("form", response.context)
        self.assertIn("password2", response.context["form"].errors)


class ProfilePageViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="password123")
        self.profile_url = reverse("library:profile")

    def test_authenticated_user_can_access_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)

        self.assertIn("user", response.context)
        self.assertEqual(response.context["user"].username, "testuser")

    def test_unauthenticated_user_is_redirected(self):
        client_without_login = Client()
        response = client_without_login.get(self.profile_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("library:login") + "?next=" + self.profile_url
        )


class IndexPageViewTests(TestCase):
    def test_home_page_renders_correct_template(self):
        response = self.client.get(reverse("library:index_page_view"))
        self.assertEqual(response.status_code, 200)


class CatalogPageViewTests(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(
            first_name="Firstname1", last_name="Lastname1"
        )
        self.author2 = Author.objects.create(
            first_name="Firstname2", last_name="Lastname2"
        )

        self.genre1 = Genre.objects.create(genre_name="Genre1")
        self.genre2 = Genre.objects.create(genre_name="Genre2")

        self.book1 = Book.objects.create(
            title="title1",
            publication_year="2003-10-10",
            description="description1",
            quantity=1,
            price=200,
        )
        self.book1.author.add(self.author1)
        self.book1.genres.add(self.genre1)

        self.book2 = Book.objects.create(
            title="title2",
            publication_year="2003-10-10",
            description="description2",
            quantity=1,
            price=300,
        )
        self.book2.author.add(self.author2)
        self.book2.genres.add(self.genre2)

        self.list_url = reverse("library:catalog_page_view")

    def test_filter_by_genre(self):
        response = self.client.get(self.list_url, {"genre": self.genre1.id})
        self.assertEqual(response.status_code, 200)

        books_in_response = list(response.context["books"])

        self.assertEqual(len(books_in_response), 1)

        self.assertNotIn(self.book2, books_in_response)

    def test_filter_by_author(self):
        response = self.client.get(self.list_url, {"author": self.author1.id})
        self.assertEqual(response.status_code, 200)

        books_in_response = list(response.context["books"])

        self.assertEqual(len(books_in_response), 1)

        self.assertNotIn(self.book2, books_in_response)

    def test_filter_by_query(self):
        response = self.client.get(self.list_url, {"query": "title2"})
        self.assertEqual(response.status_code, 200)

        books_in_response = list(response.context["books"])

        self.assertEqual(len(books_in_response), 1)

        self.assertNotIn(self.book1, books_in_response)


class BookPageViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="password123")

        self.book1 = Book.objects.create(
            title="title1",
            publication_year="2003-10-10",
            description="description1",
            quantity=1,
            price=200,
            cover_image_url="static/assets/pics/44014ddd859a3d1efa1d9e22abd33c36.jpg",
        )

        self.book2 = Book.objects.create(
            title="title2",
            publication_year="2003-10-10",
            description="description2",
            quantity=1,
            price=200,
            cover_image_url="static/assets/pics/44014ddd859a3d1efa1d9e22abd33c36.jpg",
        )

        self.liked_book1 = LikedBook.objects.create(
            user=self.user,
            book=self.book1,
        )

        self.add_book = reverse("library:add_liked_book", kwargs={"pk": self.book2.pk})
        self.delete_book = reverse(
            "library:delete_liked_book_view", kwargs={"pk": self.book1.pk}
        )

    def test_authenticated_user_page_view(self):
        response = self.client.get(
            reverse("library:book_page_view", kwargs={"pk": self.book1.pk}),
        )
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_page_view(self):
        self.client = Client()
        self.client.logout()

        response = self.client.get(
            reverse("library:book_page_view", kwargs={"pk": self.book1.pk}),
        )
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_like_book(self):
        response = self.client.post(self.add_book)
        self.assertEqual(response.status_code, 302)

        is_liked_book = LikedBook.objects.get(user=self.user, pk=self.book2.pk)
        self.assertTrue(is_liked_book)

    def test_authenticated_user_can_unike_book(self):
        response = self.client.delete(self.delete_book)
        self.assertEqual(response.status_code, 302)

        not_exist_liked_book = LikedBook.objects.filter(
            user=self.user, pk=self.book1.pk
        )
        self.assertEqual(len(not_exist_liked_book), 0)


class PurchasePageViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client.login(username="testuser", password="password123")

        self.book1 = Book.objects.create(
            title="title1",
            publication_year="2003-10-10",
            description="description1",
            quantity=1,
            price=200,
            cover_image_url="static/assets/pics/44014ddd859a3d1efa1d9e22abd33c36.jpg",
        )

        self.book2 = Book.objects.create(
            title="title2",
            publication_year="2003-10-10",
            description="description2",
            quantity=1,
            price=200,
            cover_image_url="static/assets/pics/44014ddd859a3d1efa1d9e22abd33c36.jpg",
        )

        self.url = reverse("library:purchase_create_view")

    def test_purchase_creation_with_valid_data(self):

        form_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "books": [self.book1.pk, self.book2.pk],
        }

        response = self.client.post(self.url, form_data)

        self.assertEqual(response.status_code, 302)

        self.assertEqual(Purchase.objects.count(), 1)

        purchase = Purchase.objects.first()

        self.assertEqual(purchase.first_name, "Test")
        self.assertEqual(purchase.last_name, "User")
        self.assertEqual(purchase.email, "test@example.com")
        self.assertEqual(purchase.user, self.user)

        expected_total_amount = self.book1.price + self.book2.price
        self.assertEqual(purchase.total_amount, expected_total_amount)

        self.assertIn(self.book1, purchase.books.all())
        self.assertIn(self.book2, purchase.books.all())

    def test_form_valid_calculation_logic(self):
        view = PurchaseCreateView()
        view.request = self.client.get(self.url).wsgi_request
        view.request.user = self.user

        form_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "books": [self.book1, self.book2],
        }
        form = view.get_form_class()(data=form_data)
        self.assertTrue(form.is_valid())

        response = view.form_valid(form)

        self.assertEqual(Purchase.objects.count(), 1)
        purchase = Purchase.objects.first()

        expected_total_amount = self.book1.price + self.book2.price
        self.assertEqual(purchase.total_amount, expected_total_amount)

    def test_redirect_on_success(self):
        form_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "books": [self.book1.pk],
        }

        response = self.client.post(self.url, form_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("library:catalog_page_view"))
