from django.contrib import admin
from .models import Flight, Ticket

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'flight_number', 'departure_airport', 'arrival_airport', 'departure_time', 'status')
    list_filter = ('status', 'departure_time')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'flight', 'passenger', 'seat_number', 'price', 'status', 'paid')
    list_filter = ('status', 'paid')