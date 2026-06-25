from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from library.models import Genre, Author, Book, Borrowing, Review

User = get_user_model()


class GenreModelTest(TestCase):
    def test_genre_str(self):
        genre = Genre.objects.create(name="Fiction")
        self.assertEqual(str(genre), "Fiction")


class AuthorModelTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            first_name="George", last_name="Orwell"
        )

    def test_author_str(self):
        self.assertEqual(str(self.author), "George Orwell")

    def test_full_name_property(self):
        self.assertEqual(self.author.full_name, "George Orwell")


class BookModelTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name="Frank", last_name="Herbert")
        self.genre = Genre.objects.create(name="Sci-Fi")
        self.book = Book.objects.create(
            title="Dune",
            cover=Book.CoverType.SOFT,
            inventory=5,
            daily_fee=Decimal("0.75"),
        )
        self.book.authors.add(self.author)
        self.book.genres.add(self.genre)

    def test_book_str(self):
        self.assertEqual(str(self.book), "Dune")

    def test_book_cover_default(self):
        self.assertEqual(self.book.cover, Book.CoverType.SOFT)


class BorrowingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.book = Book.objects.create(
            title="1984", inventory=3, daily_fee=Decimal("0.50")
        )
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=date.today() + timedelta(days=14),
        )

    def test_borrowing_str(self):
        self.assertIn("test@test.com", str(self.borrowing))
        self.assertIn("1984", str(self.borrowing))

    def test_is_overdue_false_for_future_date(self):
        self.assertFalse(self.borrowing.is_overdue)

    def test_is_overdue_true_for_past_date(self):
        self.borrowing.expected_return_date = date.today() - timedelta(days=1)
        self.borrowing.save()
        self.assertTrue(self.borrowing.is_overdue)

    def test_calculate_fine_zero_when_not_overdue(self):
        self.assertEqual(self.borrowing.calculate_fine(), 0)

    def test_calculate_fine_nonzero_when_overdue(self):
        self.borrowing.expected_return_date = date.today() - timedelta(days=3)
        self.borrowing.save()
        expected_fine = 3 * Decimal("0.50") * 2
        self.assertEqual(self.borrowing.calculate_fine(), expected_fine)

    def test_is_overdue_false_when_returned(self):
        self.borrowing.actual_return_date = date.today()
        self.borrowing.expected_return_date = date.today() - timedelta(days=1)
        self.assertFalse(self.borrowing.is_overdue)
