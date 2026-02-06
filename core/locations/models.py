from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=5, unique=True)
    def __str__(self): return self.name

class Airport(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='airports')
    def __str__(self): return f"{self.name} ({self.code})"
