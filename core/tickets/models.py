from django.db import models
from flights.models import Flight  
from users.models import User      

class Ticket(models.Model):
    
   
    class Status(models.TextChoices):
        BOOKED = 'booked', 'Booked'      
        CANCELLED = 'cancelled', 'Cancelled' 
        USED = 'used', 'Used'           
        PAID = 'paid', 'Paid'           

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

    
    def __str__(self):
        return f"Ticket {self.id} - {self.passenger.username} ({self.flight.flight_number})"
