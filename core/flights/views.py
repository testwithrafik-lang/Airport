from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Flight, Ticket
from .serializers import (  FlightSerializer, TicketCreateSerializer,TicketListSerializer, TicketDetailSerializer)
from users.permissions import IsAdmin, IsOwnerOrAdmin

class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticatedOrReadOnly()]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()

    def get_queryset(self):
        
        if self.request.user.is_staff or getattr(self.request.user, 'role', None) == 'ADMIN':
            return Ticket.objects.all()
        return Ticket.objects.filter(passenger=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        if self.action == 'list':
            return TicketListSerializer
        return TicketDetailSerializer

    def perform_create(self, serializer):
        serializer.save(passenger=self.request.user)

    def get_permissions(self):
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        ticket = self.get_object()
        if ticket.paid:
            return Response({'detail': 'Ticket is already paid.'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.paid = True
        ticket.status = 'confirmed'
        ticket.save()
        return Response({'detail': 'Ticket paid successfully.'}, status=status.HTTP_200_OK)