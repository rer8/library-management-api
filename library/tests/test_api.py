from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
from library.models import Genre, Author, Book, Borrowing, Review

User = get_user_model()

BOOKS_URL = "/api/library/books/"
AUTHORS_URL = "/api/library/authors/"
GENRES_URL = "/api/library/genres/"
BORROWINGS_URL = "/api/library/borrowings/"
REVIEWS_URL = "/api/library/reviews/"


def detail_url(base, pk):
    return f"{base}{pk}/"


def create_user(email="user@test.com", password="testpass123", is_staff=False):
    user = User.objects.create_user(
        username=email.split("@")[0], email=email, password=password
    )
    user.is_staff = is_staff
    user.save()
    return user


def create_book(**kwargs):
    defaults = {"title": "Test Book", "inventory": 5, "daily_fee": Decimal("0.50")}
    defaults.update(kwargs)
    return Book.objects.create(**defaults)


class PublicBookAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_books_unauthenticated(self):
        res = self.client.get(BOOKS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_book_unauthenticated_forbidden(self):
        payload = {"title": "New Book", "inventory": 1, "daily_fee": "0.50", "cover": "SOFT"}
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminBookAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = create_user("admin@test.com", is_staff=True)
        self.client.force_authenticate(self.admin)

    def test_create_book_as_admin(self):
        author = Author.objects.create(first_name="Test", last_name="Author")
        genre = Genre.objects.create(name="Fiction")
        payload = {
            "title": "New Book",
            "authors": [author.id],
            "genres": [genre.id],
            "cover": "SOFT",
            "inventory": 3,
            "daily_fee": "0.60",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(Book.objects.first().title, "New Book")

    def test_delete_book_as_admin(self):
        book = create_book()
        res = self.client.delete(detail_url(BOOKS_URL, book.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())


class BookFilterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.genre1 = Genre.objects.create(name="Fiction")
        self.genre2 = Genre.objects.create(name="Sci-Fi")
        self.book1 = create_book(title="Book A", inventory=3, daily_fee=Decimal("0.50"))
        self.book1.genres.add(self.genre1)
        self.book2 = create_book(title="Book B", inventory=0, daily_fee=Decimal("1.00"))
        self.book2.genres.add(self.genre2)

    def test_filter_available_books(self):
        res = self.client.get(BOOKS_URL, {"available": "true"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        titles = [b["title"] for b in res.data]

        self.assertTrue(any(title == "Book A" for title in titles))
        self.assertFalse(any(title == "Book B" for title in titles))

    def test_filter_by_genre(self):
        res = self.client.get(BOOKS_URL, {"genres": self.genre2.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        titles = [b["title"] for b in res.data]

        self.assertTrue(any(title == "Book B" for title in titles))
        self.assertFalse(any(title == "Book A" for title in titles))


class BorrowingAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("borrower@test.com")
        self.admin = create_user("admin@test.com", is_staff=True)
        self.book = create_book(inventory=5)

    def test_create_borrowing(self):
        self.client.force_authenticate(self.user)
        payload = {
            "book": self.book.id,
            "expected_return_date": (date.today() + timedelta(days=14)).isoformat(),
        }
        res = self.client.post(BORROWINGS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 4)

    def test_create_borrowing_no_inventory(self):
        self.client.force_authenticate(self.user)
        self.book.inventory = 0
        self.book.save()
        payload = {
            "book": self.book.id,
            "expected_return_date": (date.today() + timedelta(days=14)).isoformat(),
        }
        res = self.client.post(BORROWINGS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_sees_only_own_borrowings(self):
        other_user = create_user("other@test.com")
        Borrowing.objects.create(
            book=self.book, user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.book.inventory -= 1
        self.book.save()
        Borrowing.objects.create(
            book=self.book, user=other_user,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.client.force_authenticate(self.user)
        res = self.client.get(BORROWINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(res.data), 1)

    def test_admin_sees_all_borrowings(self):
        other_user = create_user("other2@test.com")
        Borrowing.objects.create(
            book=self.book, user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.book.inventory -= 1
        self.book.save()
        Borrowing.objects.create(
            book=self.book, user=other_user,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.client.force_authenticate(self.admin)
        res = self.client.get(BORROWINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(res.data), 2)

    def test_return_book(self):
        self.client.force_authenticate(self.user)
        borrowing = Borrowing.objects.create(
            book=self.book, user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.book.inventory -= 1
        self.book.save()
        res = self.client.post(
            f"{BORROWINGS_URL}{borrowing.id}/return/", {"confirm": True}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.status, Borrowing.Status.RETURNED)
        self.assertIsNotNone(borrowing.actual_return_date)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 5)

    def test_return_already_returned_book(self):
        self.client.force_authenticate(self.user)
        borrowing = Borrowing.objects.create(
            book=self.book, user=self.user,
            expected_return_date=date.today() + timedelta(days=7),
            status=Borrowing.Status.RETURNED,
            actual_return_date=date.today(),
        )
        res = self.client.post(
            f"{BORROWINGS_URL}{borrowing.id}/return/", {"confirm": True}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("reviewer@test.com")
        self.book = create_book()

    def test_create_review(self):
        self.client.force_authenticate(self.user)
        payload = {"book": self.book.id, "rating": 5, "comment": "Excellent!"}
        res = self.client.post(REVIEWS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_cannot_review_same_book_twice(self):
        self.client.force_authenticate(self.user)
        Review.objects.create(book=self.book, user=self.user, rating=4)
        payload = {"book": self.book.id, "rating": 3, "comment": "Again"}
        res = self.client.post(REVIEWS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_rating_rejected(self):
        self.client.force_authenticate(self.user)
        payload = {"book": self.book.id, "rating": 6}
        res = self.client.post(REVIEWS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class UserAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        payload = {
            "email": "new@test.com",
            "username": "newuser",
            "password": "strongpass123",
            "password2": "strongpass123",
        }
        res = self.client.post("/api/user/register/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new@test.com").exists())

    def test_register_password_mismatch(self):
        payload = {
            "email": "bad@test.com",
            "username": "baduser",
            "password": "pass1",
            "password2": "pass2",
        }
        res = self.client.post("/api/user/register/", payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtain_token(self):
        create_user("tokenuser@test.com", "testpass123")
        payload = {"email": "tokenuser@test.com", "password": "testpass123"}
        res = self.client.post("/api/user/token/", payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_profile_requires_auth(self):
        res = self.client.get("/api/user/me/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
