from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from flights.models import Flight
from flights.serializers import FlightSerializer


class FlightAPIView(APIView):

    def get(self, request, pk=None):
        try:
            
            if pk is not None:
                flight = Flight.objects.get(pk=pk)
                serializer = FlightSerializer(flight)
                return Response(serializer.data, status=status.HTTP_200_OK)

            
            flights = Flight.objects.all()
            serializer = FlightSerializer(flights, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Flight.DoesNotExist:
            return Response(
                {"error": "Flight not found"},
                status=status.HTTP_404_NOT_FOUND
            )
