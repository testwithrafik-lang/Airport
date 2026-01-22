from django.contrib import admin
from .models import Airplane

@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = ['model', 'registration_number', 'airline', 'capacity']
