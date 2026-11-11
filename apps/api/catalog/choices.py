from django.db import models


class PatternType(models.TextChoices):
    APRON = "APRON"
    SHIRT = "SHIRT"
    PANTS = "PANTS"
    JACKET = "JACKET"
    DRESS = "DRESS"
    OTHER = "OTHER"
