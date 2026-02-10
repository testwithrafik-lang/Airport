from django.db import models
from django.conf import settings
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

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )

    def __str__(self):
        return f"{self.flight_number}: {self.departure_airport.code} → {self.arrival_airport.code}"

class Ticket(models.Model):
    flight = models.ForeignKey(
        Flight, 
        on_delete=models.CASCADE, 
        related_name='tickets'
    )
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    seat_number = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='booked')
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Ticket {self.id} for {self.flight.flight_number}"
