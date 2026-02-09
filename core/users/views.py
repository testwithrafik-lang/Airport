from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
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
