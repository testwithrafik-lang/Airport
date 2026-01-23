from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from countries.models import Country
from countries.serializers import CountrySerializer

class CountryAPIView(APIView):

    def get(self, request, pk=None):
      
        if pk is not None:
            countries = Country.objects.all()
            serializer = CountrySerializer(countries, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        countries = Country.objects.all()[:3]
        serializer = CountrySerializer(countries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
