from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from apps.orders.choices import GarmentType

from .choices import PatternType

HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$", message="Color code must look like #RRGGBB."
)


class Pattern(models.Model):
    name = models.CharField(max_length=120)
    pattern_type = models.CharField(max_length=20, choices=PatternType.choices)
    piece_count = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Amount of pieces")
    pattern_metric = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=60)
    code = models.CharField(max_length=7, unique=True, validators=[HEX_COLOR_VALIDATOR])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs) -> None:
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Inspection(models.Model):
    """A QA checklist item that applies to one garment type."""

    name = models.CharField(max_length=120)
    garment_type = models.CharField(max_length=20, choices=GarmentType.choices)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["garment_type", "name"]

    def __str__(self) -> str:
        return f"{self.garment_type}: {self.name}"
