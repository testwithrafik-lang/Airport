from django.contrib import admin
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'passenger', 'flight', 'seat_number', 'status', 'paid']
    list_filter = ['status', 'paid']
    search_fields = ['passenger__email', 'flight__flight_number']
