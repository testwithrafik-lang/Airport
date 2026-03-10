import random
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.mail import send_mail
from .models import User
from .serializers import ( UserRegisterSerializer,UserMeSerializer, UserAdminSerializer)
from .permissions import IsAdmin, IsOwnerOrAdmin

class UserViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "ADMIN":
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        if self.request.user.is_staff or getattr(self.request.user, "role", None) == "ADMIN":
            return UserAdminSerializer
        return UserMeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='request-email-change')
    def request_email_change(self, request):
        new_email = request.data.get('new_email')
        if not new_email:
            return Response({"error": "New email is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user
        code = str(random.randint(100000, 999999))
        user.new_email = new_email
        user.email_confirm_code = code
        user.save()

        send_mail(
            "Confirm your new email address",
            f"Your confirmation code is: {code}",
            None,
            [new_email]
        )
        return Response({"detail": "Confirmation code sent to the new email address"})

    @action(detail=False, methods=['post'], url_path='confirm-email-change')
    def confirm_email_change(self, request):
        code = request.data.get('code')
        user = request.user

        if user.email_confirm_code == code and code:
            user.email = user.new_email
            user.new_email = None
            user.email_confirm_code = None
            user.save()
            return Response({"detail": "Email address updated successfully"})
        
        return Response({"error": "Invalid confirmation code"}, status=status.HTTP_400_BAD_REQUEST)