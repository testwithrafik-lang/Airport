from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets 
from .models import Country, Airport
from .serializers import CountrySerializer, AirportSerializer

class CountryAPIView(APIView):

    def get(self, request, pk=None):
        try:
            
            if pk is not None:
               
                country = Country.objects.get(pk=pk)
                serializer = CountrySerializer(country)
                return Response(serializer.data, status=status.HTTP_200_OK)

            
            countries = Country.objects.all()
            serializer = CountrySerializer(countries, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Country.DoesNotExist:
            return Response(  {"error": "Country not found"},)

class AirportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer