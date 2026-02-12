import re
from decimal import Decimal
from datetime import date
from rest_framework import serializers
from .models import Flight, Ticket, Order


SEAT_REGEX = r'^[1-9]\d?[A-F]$'

class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = [
            'id',
            'flight_number',
            'airplane',
            'departure_airport',
            'arrival_airport',
            'departure_time',
            'arrival_time',
            'base_price',
            'status',
        ]
        
        read_only_fields = ['status']

    def validate(self, attrs):
        departure_time = attrs.get('departure_time')
        arrival_time = attrs.get('arrival_time')
       

        if departure_time and departure_time.date() < date.today():
            raise serializers.ValidationError("Departure time cannot be in the past.")
        if departure_time and arrival_time and arrival_time < departure_time:
            raise serializers.ValidationError("Arrival time cannot be before departure time.")

        return attrs


class OrderTicketCreateSerializer(serializers.Serializer):
    flight = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all())
    seat_number = serializers.CharField(max_length=10)
    ticket_class = serializers.ChoiceField(choices=Ticket.Class.choices)

    def validate(self, attrs):
        flight = attrs.get('flight')
        seat_number = attrs.get('seat_number')

        if not re.match(SEAT_REGEX, seat_number or ''):
            raise serializers.ValidationError(
                {"seat_number": "Invalid seat format. Example: 12A"}
            )

        if flight.status not in [
            Flight.Status.SCHEDULED,
            Flight.Status.BOARDING,
        ]:
            raise serializers.ValidationError(
                {"flight": "Cannot buy ticket: flight is not available."}
            )

        if Ticket.objects.filter(flight=flight, seat_number=seat_number).exists():
            raise serializers.ValidationError(
                {"seat_number": f"Seat {seat_number} is already taken on this flight."}
            )

        return attrs


class TicketListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
           'id',
            'order',
            'flight',
            'seat_number',
            'ticket_class',
            'price',
            'paid',
        ]
class TicketDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['price', 'paid','order']
        flight = FlightSerializer(read_only=True)

class OrderSerializer(serializers.ModelSerializer):
    tickets = OrderTicketCreateSerializer(many=True, write_only=True)
    tickets_info = TicketListSerializer(
        many=True,
        read_only=True,
        source='tickets'
    )

    class Meta:
        model = Order
        fields = [
            'id',
            'currency',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
            'tickets',
            'tickets_info',
        ]
        read_only_fields = [
            'id',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
            'tickets_info',
        ]

    def validate_tickets(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one ticket.")
        return value

    def validate(self, attrs):
        seen = set()
        for t in attrs['tickets']:
            key = (t['flight'].id, t['seat_number'])
            if key in seen:
                raise serializers.ValidationError("Duplicate seats in one order.")
            seen.add(key)
        return attrs

    def create(self, validated_data):
        from django.db import transaction

        tickets_data = validated_data.pop('tickets')
        user = self.context['request'].user

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                currency=validated_data.get('currency', 'USD'),
                status=Order.Status.PENDING,
                total_amount=Decimal('0.00'),
            )

            total = Decimal('0.00')

            for ticket_data in tickets_data:
                flight = ticket_data['flight']
                ticket_class = ticket_data['ticket_class']

                price = flight.base_price
                if ticket_class == Ticket.Class.BUSINESS:
                    price = flight.base_price * Decimal('2.0')

                Ticket.objects.create(
                    order=order,
                    flight=flight,
                    seat_number=ticket_data['seat_number'],
                    ticket_class=ticket_class,
                    price=price,
                    paid=False,
                )

                total += price

            order.total_amount = total
            order.save(update_fields=['total_amount', 'updated_at'])

        return order