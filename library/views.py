from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Genre, Author, Book, Borrowing, Review
from .serializers import (
    GenreSerializer,
    AuthorSerializer,
    AuthorListSerializer,
    BookSerializer,
    BookListSerializer,
    BookDetailSerializer,
    BorrowingSerializer,
    BorrowingDetailSerializer,
    ReturnBorrowingSerializer,
    ReviewSerializer,
)
from .filters import BookFilter, BorrowingFilter
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["first_name", "last_name"]
    ordering_fields = ["last_name", "first_name", "birth_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return AuthorListSerializer
        return AuthorSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.prefetch_related("authors", "genres", "reviews")
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookFilter
    search_fields = ["title", "authors__last_name", "description"]
    ordering_fields = ["title", "daily_fee", "published_year", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        if self.action == "retrieve":
            return BookDetailSerializer
        return BookSerializer

    @extend_schema(
        responses={200: ReviewSerializer(many=True)},
        description="List all reviews for this book.",
    )
    @action(detail=True, methods=["get"], url_path="reviews")
    def reviews(self, request, pk=None):
        book = self.get_object()
        reviews = book.reviews.select_related("user")
        serializer = ReviewSerializer(reviews, many=True, context={"request": request})
        return Response(serializer.data)


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BorrowingFilter
    ordering_fields = ["borrow_date", "expected_return_date", "status"]

    def get_queryset(self):
        user = self.request.user
        qs = Borrowing.objects.select_related("book", "user")
        if user.is_staff:
            return qs
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "return_book":
            return ReturnBorrowingSerializer
        return BorrowingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        request=ReturnBorrowingSerializer,
        responses={200: BorrowingDetailSerializer},
        description="Mark the borrowing as returned. Only the borrower or an admin can do this.",
    )
    @action(detail=True, methods=["post"], url_path="return")
    def return_book(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.status == Borrowing.Status.RETURNED:
            return Response(
                {"detail": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (request.user == borrowing.user or request.user.is_staff):
            return Response(
                {"detail": "You do not have permission to return this borrowing."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReturnBorrowingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["confirm"]:
            borrowing.actual_return_date = timezone.now().date()
            borrowing.status = Borrowing.Status.RETURNED
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()
            return Response(
                BorrowingDetailSerializer(borrowing, context={"request": request}).data
            )
        return Response(
            {"detail": "Return not confirmed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        description="List all active (non-returned) borrowings. Admin sees all; users see their own.",
        responses={200: BorrowingSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        qs = self.get_queryset().filter(status=Borrowing.Status.ACTIVE)
        serializer = BorrowingSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class ReviewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["book", "rating"]
    ordering_fields = ["created_at", "rating"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Review.objects.select_related("book", "user")
        return Review.objects.select_related("book", "user").filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        if not (request.user == review.user or request.user.is_staff):
            return Response(
                {"detail": "You can only delete your own reviews."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)
