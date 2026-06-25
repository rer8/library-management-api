from django.contrib import admin
from .models import Genre, Author, Book, Borrowing, Review


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["full_name", "birth_date"]
    search_fields = ["first_name", "last_name"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "cover", "inventory", "daily_fee", "published_year"]
    list_filter = ["cover", "genres"]
    search_fields = ["title", "authors__last_name"]
    filter_horizontal = ["authors", "genres"]


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ["book", "user", "borrow_date", "expected_return_date", "status"]
    list_filter = ["status"]
    search_fields = ["book__title", "user__email"]
    readonly_fields = ["borrow_date"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["book", "user", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["book__title", "user__email"]
