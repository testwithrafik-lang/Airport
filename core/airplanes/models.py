from django.db import models
from airlines.models import Airline 


class Airplane(models.Model):
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='airplanes') 
    
    model = models.CharField(max_length=50)      
    capacity = models.PositiveIntegerField()     
    registration_number = models.CharField(max_length=20, unique=True)  

    def __str__(self):
        return f"{self.model} ({self.registration_number})"
