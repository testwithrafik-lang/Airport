from django.db import models
from django.utils import timezone
from airports.models import Airport
from airplanes.models import Airplane


class Airport(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.code})"
    
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
        related_name='flights',
        null=True,
        blank=True
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

    is_active = models.BooleanField(default=True) 

    def update_status_if_needed(self):
      
        if (
            self.status != self.Status.COMPLETED
            and self.arrival_time <= timezone.now()
        ):
            self.status = self.Status.COMPLETED
            self.save(update_fields=['status'])

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active'])

    def __str__(self):
        return f"{self.flight_number}: {self.departure_airport.code} → {self.arrival_airport.code}"

