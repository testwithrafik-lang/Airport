import re
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'role', 'is_active', 'is_staff']
        read_only_fields = ['id', 'is_staff']

    def validate_email(self, value):
       
        if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$',value):
            raise serializers.ValidationError("Invalid email format.")

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")

        return value

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone must contain only digits.")

        if len(value) > 10:
            raise serializers.ValidationError("Phone must not exceed 10 digits.")

        return value
