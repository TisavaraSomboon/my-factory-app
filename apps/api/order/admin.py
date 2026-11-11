from django.contrib import admin

from .models import Order, OrderEvent


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "garment_type", "fabric_type", "status", "rework_count", "created_at"]
    list_filter = ["status", "garment_type"]
    search_fields = ["name", "requester_username"]
    inlines = [OrderEventInline]


admin.site.register(OrderEvent)
