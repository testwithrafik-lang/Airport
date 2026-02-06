from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import User
from .serializers import UserRegisterSerializer, UserMeSerializer, UserAdminSerializer
from .permissions import IsAdmin, IsOwnerOrAdmin

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserMeSerializer  

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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance != request.user and not (request.user.is_staff or getattr(request.user, "role", None) == "ADMIN"):
            return Response(
                {"detail": "You do not have permission to view this user."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
