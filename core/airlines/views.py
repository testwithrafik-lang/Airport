from rest_framework import viewsets
from .models import Airline
from .serializers import AirlineSerializer

class AirlineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer
