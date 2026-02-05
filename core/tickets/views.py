from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Ticket
from .serializers import TicketCreateSerializer, TicketListSerializer, TicketDetailSerializer
from .permissions import CanPayTicket
from users.permissions import IsOwnerOrAdmin

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action in ['create', 'pay', 'cancel']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        elif self.action == 'retrieve':
            return TicketDetailSerializer
        return TicketListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "ADMIN":
            return Ticket.objects.all()
        return Ticket.objects.filter(passenger=user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanPayTicket])
    def pay(self, request, pk=None):
        try:
            ticket = self.get_object()
        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.paid:
            return Response({"detail": "Ticket already paid."}, status=status.HTTP_400_BAD_REQUEST)

        ticket.paid = True
        ticket.status = 'paid'
        ticket.save()
        return Response(self.get_serializer(ticket).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def cancel(self, request, pk=None):
        try:
            ticket = self.get_object()
        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.status == 'cancelled':
            return Response({"detail": "Ticket already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        ticket.status = 'cancelled'
        ticket.save()
        return Response({"detail": "Ticket cancelled successfully."}, status=status.HTTP_200_OK)