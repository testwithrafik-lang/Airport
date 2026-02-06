from django.db import models

class Airline(models.Model):
    name = models.CharField(max_length=100)   
    code = models.CharField(max_length=10, unique=True)  
    country = models.CharField(max_length=50)  

    def __str__(self):
        return f"{self.name} ({self.code})"

class Airplane(models.Model):
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='airplanes') 
    model = models.CharField(max_length=50)      
    capacity = models.PositiveIntegerField()     
    registration_number = models.CharField(max_length=20, unique=True)  

    def __str__(self):
        return f"{self.model} ({self.registration_number})"