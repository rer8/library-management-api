from django.urls import path, include
from rest_framework.routers import DefaultRouter
from library.views import GenreViewSet, AuthorViewSet, BookViewSet, BorrowingViewSet, ReviewViewSet

app_name = "library"

router = DefaultRouter()
router.register("genres", GenreViewSet, basename="genre")
router.register("authors", AuthorViewSet, basename="author")
router.register("books", BookViewSet, basename="book")
router.register("borrowings", BorrowingViewSet, basename="borrowing")
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = [
    path("", include(router.urls)),
]
