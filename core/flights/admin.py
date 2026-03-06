from django.contrib import admin

from .models import Flight, Ticket, Order


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'flight_number',
        'departure_airport',
        'arrival_airport',
        'departure_time',
        'status',
    )
    list_filter = ('status', 'departure_time')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'currency',
        'total_amount',
        'status',
        'created_at',
    )
    list_filter = ('status', 'currency', 'created_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'flight',
        'seat_number',
        'ticket_class',
        'price',
        'get_status',
        
    )
    list_filter = ('flight', 'ticket_class')
    def get_status(self, obj):
        return obj.order.status
    get_status.short_description = 'Order Status'