from rest_framework import serializers

from .models import Color, Inspection, Pattern


class PatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pattern
        fields = ["id", "name", "pattern_type", "piece_count", "pattern_metric", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["id", "name", "code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value: str) -> str:
        """Store codes uppercase so uniqueness is case-insensitive."""
        value = value.upper()
        qs = Color.objects.filter(code=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A color with this code already exists.")
        return value


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspection
        fields = ["id", "name", "garment_type", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
