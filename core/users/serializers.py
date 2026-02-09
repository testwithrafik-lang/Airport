import re
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'phone']

    def validate_email(self, value):
        if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$', value):
            raise serializers.ValidationError("Invalid email format.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_phone(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone must contain only digits.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)

        refresh = RefreshToken.for_user(user)

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'role', 'is_active']


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'role', 'is_active', 'is_staff']
