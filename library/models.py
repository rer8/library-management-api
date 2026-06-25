from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    biography = models.TextField(blank=True, default="")
    photo = models.ImageField(upload_to="authors/", null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = "HARD", "Hard Cover"
        SOFT = "SOFT", "Soft Cover"

    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author, related_name="books")
    genres = models.ManyToManyField(Genre, related_name="books")
    cover = models.CharField(max_length=4, choices=CoverType.choices, default=CoverType.SOFT)
    inventory = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of physical copies available in the library",
    )
    daily_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Daily borrowing fee in USD",
    )
    published_year = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    cover_image = models.ImageField(upload_to="books/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Borrowing(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RETURNED = "RETURNED", "Returned"
        OVERDUE = "OVERDUE", "Overdue"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    borrow_date = models.DateField(default=timezone.now)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-borrow_date"]

    def __str__(self):
        return f"{self.user} borrowed '{self.book}' on {self.borrow_date}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.actual_return_date:
            return False
        return timezone.now().date() > self.expected_return_date

    def calculate_fine(self):
        """Calculate fine for overdue books."""
        from django.utils import timezone
        if not self.is_overdue:
            return 0
        overdue_days = (timezone.now().date() - self.expected_return_date).days
        return overdue_days * self.book.daily_fee * 2  # 2x daily fee as penalty


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("book", "user")

    def __str__(self):
        return f"{self.user} rated '{self.book}' {self.rating}/5"
