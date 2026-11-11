"""Input/output serializers. No business rules here, only shape validation."""
from rest_framework import serializers

from .choices import EventAction, FabricType
from .models import Order, OrderEvent


class OrderSerializer(serializers.ModelSerializer):
    sla_hours = serializers.IntegerField(read_only=True, allow_null=True)
    sla_deadline = serializers.DateTimeField(read_only=True, allow_null=True)
    is_overdue = serializers.BooleanField(read_only=True)
    next_status = serializers.CharField(read_only=True, allow_null=True)
    actor = serializers.CharField(
        write_only=True, required=False, help_text="Who made the change (defaults to requester_username)."
    )

    class Meta:
        model = Order
        fields = [
            "id", "name", "garment_type", "fabric_type", "requester_username", "address", "quantity",
            "pattern", "color", "color_metric", "status", "is_ready_dispatch",
            "measured_fabric_meters", "finished_fabric_meters", "assembled_pieces_count",
            "cartons_count", "tracking_number", "rework_count", "stage_started_at",
            "created_at", "updated_at", "sla_hours", "sla_deadline", "is_overdue", "next_status", "actor",
        ]
        read_only_fields = [
            "id", "status", "is_ready_dispatch", "measured_fabric_meters", "finished_fabric_meters",
            "assembled_pieces_count", "cartons_count", "tracking_number", "rework_count",
            "stage_started_at", "created_at", "updated_at",
        ]

    def validate_quantity(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Ensure this value is greater than or equal to 1.")
        return value


class OrderEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderEvent
        fields = ["id", "order", "status", "action", "actor", "note", "data", "created_at"]
        read_only_fields = fields


class InspectionResultSerializer(serializers.Serializer):
    inspection_id = serializers.IntegerField()
    passed = serializers.BooleanField()


class ApproveInputSerializer(serializers.Serializer):
    """Body of POST /orders/{id}/approve/. Which stage fields are needed depends on the status."""

    actor = serializers.CharField(max_length=150)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    pattern_id = serializers.IntegerField(required=False, help_text="DESIGN")
    swatch_fabric_type = serializers.ChoiceField(choices=FabricType.choices, required=False, help_text="FABRIC_PREP")
    measured_fabric_meters = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, help_text="FABRIC_PREP"
    )
    color_id = serializers.IntegerField(required=False, help_text="FABRIC_DONE")
    finished_fabric_meters = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, help_text="FABRIC_DONE"
    )
    assembled_pieces_count = serializers.IntegerField(required=False, min_value=0, help_text="STITCHING")
    results = InspectionResultSerializer(many=True, required=False, help_text="QA")
    tracking_number = serializers.CharField(required=False, allow_blank=True, help_text="PACKAGING")


class RejectInputSerializer(serializers.Serializer):
    actor = serializers.CharField(max_length=150)
    reason = serializers.CharField()


class ReadyDispatchInputSerializer(serializers.Serializer):
    actor = serializers.CharField(max_length=150)
    is_ready = serializers.BooleanField()
    cartons_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class FabricRulesSerializer(serializers.Serializer):
    """Mapping garment_type -> list of allowed fabric types."""

    GENERAL = serializers.ListField(child=serializers.CharField())
    HEAT_INSULATION = serializers.ListField(child=serializers.CharField())
    WATERPROOF = serializers.ListField(child=serializers.CharField())
    WINTER = serializers.ListField(child=serializers.CharField())
    CHEAP = serializers.ListField(child=serializers.CharField())
