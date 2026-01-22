from django.db import models


class Airline(models.Model):
    name = models.CharField(max_length=100)   
    code = models.CharField(max_length=10, unique=True)  
    country = models.CharField(max_length=50)  

    def __str__(self):
        return f"{self.name} ({self.code})"
