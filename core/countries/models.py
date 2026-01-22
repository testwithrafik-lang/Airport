from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=50)  
    code = models.CharField(max_length=5, unique=True) 

    def __str__(self):
        return f"{self.name} ({self.code})"
