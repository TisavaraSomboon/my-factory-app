"""Create demo catalog data and sample orders. Safe to run many times."""
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Color, Inspection, Pattern
from apps.orders import services
from apps.orders.choices import FabricType, GarmentType, OrderStatus
from apps.orders.models import Order

PATTERNS = [
    {"name": "Kitchen apron", "pattern_type": "APRON", "piece_count": 3, "pattern_metric": {"length_cm": 80, "width_cm": 60}},
    {"name": "Classic shirt", "pattern_type": "SHIRT", "piece_count": 9, "pattern_metric": {"chest_cm": 104}},
    {"name": "Work pants", "pattern_type": "PANTS", "piece_count": 6, "pattern_metric": {"waist_cm": 84}},
]
COLORS = [("Navy", "#000080"), ("Crimson", "#DC143C"), ("Charcoal", "#36454F")]
INSPECTIONS = {
    GarmentType.GENERAL: ["Seam strength", "Size check"],
    GarmentType.HEAT_INSULATION: ["Heat resistance test", "Seam strength"],
    GarmentType.WATERPROOF: ["Water repellency test"],
    GarmentType.WINTER: ["Insulation check"],
    GarmentType.CHEAP: ["Visual check"],
}
BASE = {"requester_username": "demo_customer", "address": "99 Rama IV Rd, Bangkok 10500"}


class Command(BaseCommand):
    help = "Seed demo patterns, colors, inspections and sample orders (idempotent)."

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        patterns = {p["name"]: Pattern.objects.get_or_create(name=p["name"], defaults=p)[0] for p in PATTERNS}
        colors = [Color.objects.get_or_create(code=code, defaults={"name": name})[0] for name, code in COLORS]
        for garment, names in INSPECTIONS.items():
            for name in names:
                Inspection.objects.get_or_create(name=name, garment_type=garment)

        self._seed_orders(patterns, colors[0])
        self.stdout.write(self.style.SUCCESS("Demo data ready."))

    def _new_order(self, name: str, garment: str, fabric: str, quantity: int, **extra: Any) -> Order | None:
        """Create the order unless one with this name already exists."""
        if Order.objects.filter(name=name).exists():
            return None
        return services.create_order(
            name=name, garment_type=garment, fabric_type=fabric, quantity=quantity, **BASE, **extra
        )

    def _advance_to(self, order: Order, target: str, patterns: dict[str, Pattern], color: Color) -> None:
        """Approve step by step until the order reaches `target`."""
        steps = {
            OrderStatus.DESIGN: lambda o: {"pattern_id": o.pattern_id or patterns["Kitchen apron"].pk},
            OrderStatus.FABRIC_PREP: lambda o: {"swatch_fabric_type": o.fabric_type, "measured_fabric_meters": "30.00"},
            OrderStatus.FABRIC_DONE: lambda o: {"color_id": color.pk, "finished_fabric_meters": "28.50"},
            OrderStatus.STITCHING: lambda o: {"assembled_pieces_count": o.quantity},
            OrderStatus.QA: lambda o: {"results": [
                {"inspection_id": i.pk, "passed": True}
                for i in Inspection.objects.filter(garment_type=o.garment_type)]},
        }
        while order.status != target:
            order = Order.objects.get(pk=order.pk)
            if order.status == OrderStatus.PACKAGING:
                order = services.set_ready_dispatch(order, "seed", True, cartons_count=2)
                data = {"tracking_number": f"TH{order.pk:09d}"}
            else:
                data = steps[order.status](order)
            order = services.approve(order, "seed", "seeded", **data)

    def _seed_orders(self, patterns: dict[str, Pattern], color: Color) -> None:
        apron = patterns["Kitchen apron"]
        plan = [
            ("Demo: kitchen apron (new)", GarmentType.HEAT_INSULATION, FabricType.COTTON, 20, OrderStatus.DESIGN),
            ("Demo: kitchen apron (fabric prep)", GarmentType.HEAT_INSULATION, FabricType.ARAMID, 15, OrderStatus.FABRIC_PREP),
            ("Demo: rain jacket (stitching)", GarmentType.WATERPROOF, FabricType.NYLON, 8, OrderStatus.STITCHING),
            ("Demo: winter coat (QA)", GarmentType.WINTER, FabricType.WOOL, 5, OrderStatus.QA),
            ("Demo: shirts (packaging)", GarmentType.GENERAL, FabricType.LINEN, 12, OrderStatus.PACKAGING),
            ("Demo: work pants (delivered)", GarmentType.CHEAP, FabricType.COTTON, 30, OrderStatus.DELIVERED),
        ]
        for name, garment, fabric, qty, target in plan:
            order = self._new_order(name, garment, fabric, qty, pattern=apron)
            if order is not None:
                self._advance_to(order, target, patterns, color)
