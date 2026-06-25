from datetime import timedelta
import random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from faker import Faker

from library.models import (
Genre,
Author,
Book,
Borrowing,
Review,
)

fake = Faker("uk_UA")
User = get_user_model()

class Command(BaseCommand):
help = "Generate demo data for library project"


def handle(self, *args, **kwargs):

    self.stdout.write("Cleaning old data...")

    Review.objects.all().delete()
    Borrowing.objects.all().delete()
    Book.objects.all().delete()
    Author.objects.all().delete()
    Genre.objects.all().delete()

    genres = [
        "Classic",
        "Science Fiction",
        "Fantasy",
        "Mystery",
        "Thriller",
        "Adventure",
        "Historical Fiction",
        "Poetry",
        "Drama",
        "Children",
        "Non-Fiction",
        "Biography",
        "Modern Ukrainian",
        "Romance",
        "Detective",
    ]

    genre_objects = []

    for name in genres:
        genre_objects.append(
            Genre.objects.create(
                name=name,
                description=f"Genre: {name}"
            )
        )

    authors_data = [
        ("Іван", "Франко"),
        ("Леся", "Українка"),
        ("Тарас", "Шевченко"),
        ("Ліна", "Костенко"),
        ("Сергій", "Жадан"),
        ("Наталія", "Матолінець"),
        ("Володимир", "Винниченко"),
        ("Іван", "Нечуй-Левицький"),
        ("Пантелеймон", "Куліш"),
        ("Василь", "Стефаник"),
        ("Михайло", "Коцюбинський"),
        ("Ольга", "Кобилянська"),
        ("Юрій", "Андрухович"),
        ("Оксана", "Забужко"),
        ("Андрій", "Кокотюха"),
        ("Любко", "Дереш"),
        ("Марія", "Матіос"),
        ("Валерій", "Шевчук"),
        ("Артем", "Чех"),
        ("Макс", "Кідрук"),
    ]

    author_objects = []

    for first_name, last_name in authors_data:
        author_objects.append(
            Author.objects.create(
                first_name=first_name,
                last_name=last_name,
                biography=fake.text(max_nb_chars=500),
            )
        )

    if not User.objects.filter(email="admin@library.com").exists():
        User.objects.create_superuser(
            email="admin@library.com",
            username="admin",
            password="admin12345"
        )

    users = []

    for i in range(1, 16):
        email = f"reader{i}@example.com"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": f"reader{i}",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "bio": fake.sentence(),
            }
        )

        if created:
            user.set_password("password123")
            user.save()

        users.append(user)

    book_titles = [
        "Захар Беркут",
        "Борислав сміється",
        "Лісова пісня",
        "Касандра",
        "Кобзар",
        "Маруся Чурай",
        "Інтернат",
        "Варта у Грі",
        "Сонячна машина",
        "Кайдашева сім'я",
        "Чорна рада",
        "Камінний хрест",
        "Тіні забутих предків",
        "Intermezzo",
        "Царівна",
        "Музей покинутих секретів",
        "Ворошиловград",
        "Месопотамія",
        "Червоний",
        "Залишенець",
    ]

    while len(book_titles) < 50:
        book_titles.append(fake.sentence(nb_words=3)[:255])

    books = []

    for title in book_titles:
        book = Book.objects.create(
            title=title,
            cover=random.choice(["HARD", "SOFT"]),
            inventory=random.randint(1, 20),
            daily_fee=round(random.uniform(0.3, 2.0), 2),
            published_year=random.randint(1850, 2024),
            description=fake.text(max_nb_chars=400),
        )

        book.authors.set(
            random.sample(
                author_objects,
                random.randint(1, 3)
            )
        )

        book.genres.set(
            random.sample(
                genre_objects,
                random.randint(1, 3)
            )
        )

        books.append(book)

    for _ in range(40):

        status = random.choices(
            ["RETURNED", "ACTIVE", "OVERDUE"],
            weights=[70, 20, 10],
            k=1
        )[0]

        borrow_date = timezone.now().date() - timedelta(
            days=random.randint(1, 120)
        )

        expected = borrow_date + timedelta(days=14)

        actual = None

        if status == "RETURNED":
            actual = expected - timedelta(
                days=random.randint(0, 5)
            )

        Borrowing.objects.create(
            book=random.choice(books),
            user=random.choice(users),
            borrow_date=borrow_date,
            expected_return_date=expected,
            actual_return_date=actual,
            status=status,
            notes=fake.sentence(),
        )

    for _ in range(100):

        user = random.choice(users)
        book = random.choice(books)

        Review.objects.get_or_create(
            user=user,
            book=book,
            defaults={
                "rating": random.randint(1, 5),
                "comment": fake.text(max_nb_chars=200),
            }
        )

    self.stdout.write(
        self.style.SUCCESS(
            "Demo data successfully generated."
        )
    )
