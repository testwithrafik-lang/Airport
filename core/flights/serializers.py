from rest_framework import serializers
from .models import Flight
from datetime import date

class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = [ 'id','flight_number','airplane','departure_airport','arrival_airport','departure_time','arrival_time','status']
        read_only_fields = ['status']   

    def validate(self, attrs):
        departure_time = attrs.get('departure_time')
        arrival_time = attrs.get('arrival_time')
        airplane = attrs.get('airplane')
        
        if departure_time and departure_time < date.today():
            raise serializers.ValidationError("Departure time cannot be in the past.")

        if departure_time and arrival_time and arrival_time < departure_time:
            raise serializers.ValidationError("Arrival time cannot be before departure time.")

        if airplane and airplane.capacity <= 0:
            raise serializers.ValidationError("Airplane capacity must be greater than zero.")

        return attrs
