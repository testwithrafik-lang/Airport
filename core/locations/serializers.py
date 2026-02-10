from rest_framework import serializers
from .models import Country, Airport

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name', 'code')

class AirportSerializer(serializers.ModelSerializer):
    
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), 
        source='country', 
        write_only=True
    )
    class Meta:
        model = Airport
        fields = ('id', 'name', 'code', 'city', 'country', 'country_id')