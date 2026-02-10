from rest_framework import viewsets
from .models import Airline, Airplane
from .serializers import AirlineSerializer, AirplaneSerializer

class AirlineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer

class AirplaneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
