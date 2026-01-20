from django.contrib import admin
from .models import Airline

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country']
