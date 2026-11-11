import django_filters

from . import services
from .models import Order


class OrderFilter(django_filters.FilterSet):
    overdue = django_filters.BooleanFilter(method="filter_overdue", help_text="true = past SLA deadline")

    class Meta:
        model = Order
        fields = ["status", "garment_type"]

    def filter_overdue(self, queryset, name, value):
        return services.filter_overdue(queryset, value)
