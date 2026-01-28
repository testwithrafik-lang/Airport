from django.db import models
from django.utils import timezone
from flights.models import Flight
from users.models import User


class Ticket(models.Model):

    class Status(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        PAID = 'paid', 'Paid'
        USED = 'used', 'Used'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'   

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    seat_number = models.CharField(max_length=5)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BOOKED
    )

    paid = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)  

    def update_status_if_needed(self):
      
        if (
            not self.paid
            and self.flight.departure_time <= timezone.now()
            and self.status != self.Status.EXPIRED
        ):
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status'])

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=['is_active'])

    def __str__(self):
        return f"Ticket {self.id} - {self.passenger.email} ({self.flight.flight_number})"
