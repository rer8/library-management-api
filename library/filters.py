import django_filters
from library.models import Book, Borrowing


class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")
    authors = django_filters.NumberFilter(field_name="authors__id")
    genres = django_filters.NumberFilter(field_name="genres__id")
    cover = django_filters.ChoiceFilter(choices=Book.CoverType.choices)
    min_fee = django_filters.NumberFilter(field_name="daily_fee", lookup_expr="gte")
    max_fee = django_filters.NumberFilter(field_name="daily_fee", lookup_expr="lte")
    published_year = django_filters.NumberFilter()
    available = django_filters.BooleanFilter(
        field_name="inventory", method="filter_available"
    )

    class Meta:
        model = Book
        fields = ["title", "authors", "genres", "cover", "published_year"]

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(inventory__gt=0)
        return queryset.filter(inventory=0)


class BorrowingFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Borrowing.Status.choices)
    user = django_filters.NumberFilter(field_name="user__id")
    book = django_filters.NumberFilter(field_name="book__id")
    is_active = django_filters.BooleanFilter(method="filter_active")

    class Meta:
        model = Borrowing
        fields = ["status", "user", "book"]

    def filter_active(self, queryset, name, value):
        if value:
            return queryset.filter(actual_return_date__isnull=True)
        return queryset.filter(actual_return_date__isnull=False)
