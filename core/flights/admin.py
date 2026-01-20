from django.contrib import admin
from .models import Flight

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ['flight_number', 'airplane', 'departure_airport', 'arrival_airport', 'status']
    list_filter = ['status']
