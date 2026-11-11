from datetime import datetime, timedelta

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .choices import STAGE_SLA_HOURS, EventAction, FabricType, GarmentType, NEXT_STATUS, OrderStatus


class Order(models.Model):
    name = models.CharField(max_length=160)
    garment_type = models.CharField(max_length=20, choices=GarmentType.choices)
    fabric_type = models.CharField(max_length=20, choices=FabricType.choices)
    requester_username = models.CharField(max_length=150)
    address = models.TextField()
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    pattern = models.ForeignKey("catalog.Pattern", null=True, blank=True, on_delete=models.PROTECT, related_name="orders")
    color = models.ForeignKey("catalog.Color", null=True, blank=True, on_delete=models.PROTECT, related_name="orders")
    color_metric = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.DESIGN)
    is_ready_dispatch = models.BooleanField(default=False)
    measured_fabric_meters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    finished_fabric_meters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    assembled_pieces_count = models.PositiveIntegerField(null=True, blank=True)
    cartons_count = models.PositiveIntegerField(null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    rework_count = models.PositiveIntegerField(default=0)
    stage_started_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk} {self.name} [{self.status}]"

    @property
    def sla_hours(self) -> int | None:
        return STAGE_SLA_HOURS[self.status]

    @property
    def sla_deadline(self) -> datetime | None:
        if self.sla_hours is None:
            return None
        return self.stage_started_at + timedelta(hours=self.sla_hours)

    @property
    def is_overdue(self) -> bool:
        deadline = self.sla_deadline
        return deadline is not None and timezone.now() > deadline

    @property
    def next_status(self) -> str | None:
        target = NEXT_STATUS[self.status]
        return str(target) if target else None


class OrderEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=20, choices=OrderStatus.choices)
    action = models.CharField(max_length=24, choices=EventAction.choices)
    actor = models.CharField(max_length=150)
    note = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"{self.order_id} {self.action} @ {self.status}"
