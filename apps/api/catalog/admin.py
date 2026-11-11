from django.contrib import admin

from .models import Color, Inspection, Pattern

admin.site.register(Pattern)
admin.site.register(Color)
admin.site.register(Inspection)
