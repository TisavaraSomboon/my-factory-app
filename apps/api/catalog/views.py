from rest_framework import viewsets

from .models import Color, Inspection, Pattern
from .serializers import ColorSerializer, InspectionSerializer, PatternSerializer


class PatternViewSet(viewsets.ModelViewSet):
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializer
    filterset_fields = ["pattern_type"]
    search_fields = ["name"]


class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    search_fields = ["name", "code"]


class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.all()
    serializer_class = InspectionSerializer
    filterset_fields = ["garment_type"]
