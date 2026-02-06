from rest_framework import serializers
from .models import Flight, Ticket
from datetime import date

class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ['id', 'flight_number', 'airplane', 'departure_airport', 'arrival_airport', 'departure_time', 'arrival_time', 'status']
        read_only_fields = ['status']

    def validate(self, attrs):
        departure_time = attrs.get('departure_time')
        arrival_time = attrs.get('arrival_time')
        airplane = attrs.get('airplane')
        
        if departure_time and departure_time.date() < date.today():
            raise serializers.ValidationError("Departure time cannot be in the past.")
        if departure_time and arrival_time and arrival_time < departure_time:
            raise serializers.ValidationError("Arrival time cannot be before departure time.")
        if airplane and airplane.capacity <= 0:
            raise serializers.ValidationError("Airplane capacity must be greater than zero.")
        return attrs

class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['flight', 'seat_number', 'price']

    def validate(self, attrs):
        flight = attrs.get('flight')
        seat_number = attrs.get('seat_number')

        if flight.status not in ['scheduled', 'boarding']:
            raise serializers.ValidationError({"flight": "Cannot buy ticket: flight is not available."})

        if Ticket.objects.filter(flight=flight, seat_number=seat_number).exists():
            raise serializers.ValidationError({"seat_number": f"Seat {seat_number} is already taken on this flight."})

        if flight.airplane and Ticket.objects.filter(flight=flight).count() >= flight.airplane.capacity:
            raise serializers.ValidationError({"flight": "Cannot buy ticket: airplane capacity exceeded."})

        if flight.departure_time.date() < date.today():
            raise serializers.ValidationError({"flight": "Cannot buy ticket: flight date is in the past."})

        return attrs

class TicketListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'flight', 'seat_number', 'price', 'status', 'paid']

class TicketDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['status', 'paid', 'passenger']

TicketSerializer = TicketDetailSerializer