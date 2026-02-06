from django.contrib import admin
from .models import Country, Airport

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code']
    search_fields = ['name', 'code']

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'city', 'country']
    list_filter = ['country']
    search_fields = ['name', 'code', 'city']