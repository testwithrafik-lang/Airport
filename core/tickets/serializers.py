from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['passenger', 'status', 'paid']

    def validate(self, attrs):
    
        flight = attrs.get('flight')
        seat_number = attrs.get('seat_number')

      
        if flight.status not in ['scheduled', 'boarding']:
            raise serializers.ValidationError( "Cannot buy ticket: flight is not available for booking.")
        
        if Ticket.objects.filter( flight=flight,seat_number=seat_number).exists():
            raise serializers.ValidationError(f"Seat {seat_number} is already taken on this flight.")

        if flight.airplane:
            booked = Ticket.objects.filter(flight=flight).count()
            if booked >= flight.airplane.capacity:
                raise serializers.ValidationError("Cannot buy ticket: airplane capacity exceeded.")

        return attrs
