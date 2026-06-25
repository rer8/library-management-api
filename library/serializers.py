from rest_framework import serializers
from django.utils import timezone
from .models import Genre, Author, Book, Borrowing, Review


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "description"]


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "first_name", "last_name", "birth_date", "biography", "photo"]


class AuthorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "full_name", "photo"]


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id", "title", "authors", "genres", "cover",
            "inventory", "daily_fee", "published_year",
            "description", "cover_image", "created_at",
        ]


class BookListSerializer(serializers.ModelSerializer):
    authors = AuthorListSerializer(many=True, read_only=True)
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id", "title", "authors", "genres", "cover",
            "inventory", "daily_fee", "published_year",
            "cover_image", "average_rating",
        ]

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)


class BookDetailSerializer(BookListSerializer):
    class Meta(BookListSerializer.Meta):
        fields = BookListSerializer.Meta.fields + ["description", "created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "book", "user", "user_email", "rating", "comment", "created_at"]
        read_only_fields = ["user", "created_at"]

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        book = attrs.get("book")
        if Review.objects.filter(book=book, user=request.user).exists():
            raise serializers.ValidationError(
                "You have already reviewed this book."
            )
        return attrs


class BorrowingSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    fine = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = [
            "id", "book", "book_title", "user", "user_email",
            "borrow_date", "expected_return_date", "actual_return_date",
            "status", "notes", "fine",
        ]
        read_only_fields = ["user", "borrow_date", "actual_return_date", "status"]

    def get_fine(self, obj):
        return str(obj.calculate_fine())

    def validate(self, attrs):
        book = attrs.get("book")
        if book and book.inventory < 1:
            raise serializers.ValidationError(
                f"'{book.title}' is currently not available (no inventory)."
            )
        expected = attrs.get("expected_return_date")
        if expected and expected <= timezone.now().date():
            raise serializers.ValidationError(
                "Expected return date must be in the future."
            )
        return attrs

    def create(self, validated_data):
        book = validated_data["book"]
        book.inventory -= 1
        book.save()
        return super().create(validated_data)


class ReturnBorrowingSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(
        help_text="Set to true to confirm the book return."
    )


class BorrowingDetailSerializer(BorrowingSerializer):
    book = BookListSerializer(read_only=True)
