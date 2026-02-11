from django.db import models
from django.conf import settings
from decimal import Decimal

from locations.models import Airport
from fleet.models import Airplane


class Flight(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        BOARDING = 'boarding', 'Boarding'
        DEPARTED = 'departed', 'Departed'
        DELAYED = 'delayed', 'Delayed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    flight_number = models.CharField(max_length=20, unique=True)
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name='flights'
    )
    departure_airport = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name='departures'
    )
    arrival_airport = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name='arrivals'
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )

    def __str__(self):
        return f"{self.flight_number}: {self.departure_airport.code} → {self.arrival_airport.code}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        CANCELED = 'CANCELED', 'Canceled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    currency = models.CharField(max_length=3, default='USD')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.user}"


class Ticket(models.Model):
    class Class(models.TextChoices):
        ECONOMY = 'economy', 'Economy'
        STANDARD = 'standard', 'Standard'
        BUSINESS = 'business', 'Business'

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    seat_number = models.CharField(max_length=10)
    ticket_class = models.CharField(
        max_length=10,
        choices=Class.choices,
        default=Class.ECONOMY
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False
    )

    class Meta:
        unique_together = ('flight', 'seat_number')

    def save(self, *args, **kwargs):
        ratios = {
            self.Class.ECONOMY: Decimal('1.0'),
            self.Class.STANDARD: Decimal('1.3'),
            self.Class.BUSINESS: Decimal('2.5'),
        }
        self.price = self.flight.base_price * ratios[self.ticket_class]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket {self.id} for {self.flight.flight_number}"
