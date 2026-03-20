import re
from decimal import Decimal
from datetime import date, timedelta
from typing import Any
from rest_framework import serializers
from .models import Flight, Ticket, Order
from django.db import transaction
from django.utils import timezone

SEAT_REGEX = r'^[1-9]\d?[A-F]$'

class FlightSerializer(serializers.ModelSerializer):
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'airplane', 'departure_airport',
            'arrival_airport', 'departure_time', 'arrival_time',
            'base_price', 'status', 'tickets_available',
        ]
        read_only_fields = ['status', 'tickets_available']

    def validate(self, attrs):
        departure_time = attrs.get('departure_time')
        arrival_time = attrs.get('arrival_time')
        if departure_time and departure_time.date() < date.today():
            raise serializers.ValidationError("Departure time cannot be in the past.")
        if departure_time and arrival_time and arrival_time < departure_time:
            raise serializers.ValidationError("Arrival time cannot be before departure time.")
        return attrs

class TicketListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'seat_number', 'ticket_class', 'price']

class TicketDetailSerializer(serializers.ModelSerializer):
    flight = FlightSerializer(read_only=True)
    class Meta:
        model = Ticket
        fields = ['id', 'flight', 'seat_number', 'ticket_class', 'price']
class OrderTicketCreateSerializer(serializers.Serializer):
    flight = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all())
    seat_number = serializers.CharField(max_length=10)
    ticket_class = serializers.ChoiceField(choices=Ticket.Class.choices)

    def validate(self, attrs):
        flight = attrs.get('flight')
        seat_number = attrs.get('seat_number')
        airplane = flight.airplane

       
        if not re.match(SEAT_REGEX, seat_number or ''):
            raise serializers.ValidationError({"seat_number": "Invalid seat format. Example: 12A"})
        
        
        try:
            row = int(seat_number[:-1])
            letter = seat_number[-1]
            seat_in_row = ord(letter) - ord('A') + 1
        except (ValueError, IndexError):
            raise serializers.ValidationError({"seat_number": "Invalid seat format."})

       
        if row > airplane.rows:
            raise serializers.ValidationError({"seat_number": f"Row {row} exceeds airplane rows ({airplane.rows})"})
        if seat_in_row > airplane.seats_in_row:
            raise serializers.ValidationError({"seat_number": f"Seat {letter} exceeds seats per row ({airplane.seats_in_row})"})

        
        if flight.status not in [Flight.Status.SCHEDULED, Flight.Status.BOARDING]:
            raise serializers.ValidationError({"flight": "Cannot buy ticket: flight is not available."})
        
    
        if Ticket.objects.filter(
            flight=flight, 
            seat_number=seat_number,
            order__status__in=[Order.Status.PAID, Order.Status.PENDING, Order.Status.CONFIRMED]
        ).exists():
            raise serializers.ValidationError({"seat_number": f"Seat {seat_number} is already taken."})
        
        return attrs
class OrderSerializer(serializers.ModelSerializer):
    tickets = OrderTicketCreateSerializer(many=True, write_only=True)
    tickets_info = TicketListSerializer(many=True, read_only=True, source='tickets')

    class Meta:
        model = Order
        fields = [
            'id', 'currency', 'total_amount', 'status',
            'created_at', 'updated_at', 'reserved_until',
            'tickets', 'tickets_info',
        ]
        read_only_fields = ['id', 'total_amount', 'status', 'created_at', 'updated_at', 'tickets_info']

    def validate(self, attrs):
        seen = set()
        for t in attrs['tickets']:
            key = (t['flight'].id, t['seat_number'])
            if key in seen:
                raise serializers.ValidationError("Duplicate seats in one order.")
            seen.add(key)
        return attrs

    def create(self, validated_data):
        tickets_data = validated_data.pop('tickets')
        user = self.context['request'].user
        
        Order.objects.filter(status=Order.Status.PENDING, reserved_until__lt=timezone.now()).update(status=Order.Status.EXPIRED)

        with transaction.atomic():
            flight_ids = [t['flight'].id for t in tickets_data]
            list[Any](Flight.objects.filter(id__in=flight_ids).select_for_update())
            order = Order.objects.create(
                user=user,
                currency=validated_data.get('currency', 'USD'),
                reserved_until=timezone.now() + timedelta(minutes=10)
            )
            total_amount = Decimal('0.00')
            for ticket_data in tickets_data:
                ticket = Ticket.objects.create(
                    order=order,
                    flight=ticket_data['flight'],
                    seat_number=ticket_data['seat_number'],
                    ticket_class=ticket_data['ticket_class']
                )
                total_amount += ticket.price
            
            order.total_amount = total_amount
            order.save(update_fields=['total_amount', 'updated_at'])
            return order