from rest_framework import serializers
from .models import Airline, Airplane

class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ['id', 'name', 'code', 'country']

class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ['id', 'airline', 'model', 'capacity', 'registration_number']