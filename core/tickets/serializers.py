from rest_framework import serializers
from .models import Ticket
from datetime import date

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
