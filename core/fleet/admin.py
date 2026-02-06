from django.contrib import admin
from .models import Airline, Airplane

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'country')
    search_fields = ('name', 'code')

@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    # Тут я вказав саме ті поля, які є у твоєму коді: 'model' та 'registration_number'
    list_display = ('id', 'model', 'registration_number', 'capacity', 'airline')
    list_filter = ('airline',)
    search_fields = ('model', 'registration_number')