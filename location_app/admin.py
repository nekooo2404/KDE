from django.contrib import admin
from .models import LocationTerm


@admin.register(LocationTerm)
class LocationTermAdmin(admin.ModelAdmin):
    list_display = ('term', 'city', 'density', 'latitude', 'longitude')
    search_fields = ('term', 'city')
