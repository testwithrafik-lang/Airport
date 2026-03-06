from django.db import models
from django.conf import settings
from decimal import Decimal
from locations.models import Airport
from fleet.models import Airplane
from django.utils import timezone
from datetime import timedelta
from django.db.models import UniqueConstraint

class Flight(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        BOARDING = 'boarding', 'Boarding'
        DEPARTED = 'departed', 'Departed'
        DELAYED = 'delayed', 'Delayed'
        CANCELED = 'canceled', 'Canceled'
        COMPLETED = 'completed', 'Completed'

    flight_number = models.CharField(max_length=20, unique=True)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name='flights')
    departure_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='departures')
    arrival_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='arrivals')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    def __str__(self):
        return f"{self.flight_number}: {self.departure_airport.code} → {self.arrival_airport.code}"
    
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        CANCELED = 'CANCELED', 'Canceled'
        EXPIRED = 'EXPIRED', 'Expired'
        CONFIRMED = 'CONFIRMED', 'Confirmed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    currency = models.CharField(max_length=3, default='USD')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reserved_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.reserved_until = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def if_expired(self):
        return self.status == self.Status.PENDING and timezone.now() > self.reserved_until
    
    def expire(self):
        if self.status == self.Status.PENDING:
            self.status = self.Status.EXPIRED 
            self.save()
    def get_refund_percentage(self):
       
        first_ticket = self.tickets.select_related('flight').first()
        if not first_ticket:
            return 0
        
        now = timezone.now()
        departure = first_ticket.flight.departure_time
        time_diff = departure - now

        if time_diff > timedelta(hours=2):
            return 100 
        elif timedelta(hours=1) <= time_diff <= timedelta(hours=2):
            return 50   
        else:
            return 0

    def cancel(self):
        if self.status in [self.Status.CONFIRMED, self.Status.EXPIRED]:
            raise ValueError("Order cannot be canceled")
        self.status = self.Status.CANCELED
        self.save()
        

    def __str__(self):
        return f"Order {self.id} by {self.user}"


class Ticket(models.Model):
    class Class(models.TextChoices):
        ECONOMY = 'economy', 'Economy'
        STANDARD = 'standard', 'Standard'
        BUSINESS = 'business', 'Business'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tickets')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='tickets')
    seat_number = models.CharField(max_length=10)
    ticket_class = models.CharField(max_length=10, choices=Class.choices, default=Class.ECONOMY)
    price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.ticket_class = self.ticket_class.lower().strip()
        self.seat_number = self.seat_number.strip().upper()
        active_booking = Ticket.objects.filter(
            flight=self.flight,
            seat_number=self.seat_number,
            order__status__in=['PENDING', 'PAID', 'CONFIRMED']
        )
        if self.pk:
            active_booking = active_booking.exclude(pk=self.pk)
            original = Ticket.objects.get(pk=self.pk)
            if original.order.status == Order.Status.CONFIRMED:
                raise ValueError("Cannot change ticket in a confirmed order.")

        if active_booking.exists():
            raise ValueError(f"Seat {self.seat_number} is already reserved.")

        ratios = {
            'economy': Decimal('1.0'),
            'standard': Decimal('1.5'),
            'business': Decimal('2.5'),
        }
        if self.ticket_class not in ratios:
            raise ValueError("Invalid ticket class.")
        self.price = self.flight.base_price * ratios[self.ticket_class]
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        