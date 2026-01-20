from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets
from .models import Airport
from .serializers import AirportSerializer

class AirportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
