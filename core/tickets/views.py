from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Ticket
from .serializers import TicketSerializer
from users.permissions import IsOwnerOrAdmin
from .permissions import CanPayTicket

class TicketViewSet(ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) == "ADMIN":
            return Ticket.objects.all()
        return Ticket.objects.filter(passenger=user)

    def perform_create(self, serializer):
        serializer.save(
            passenger=self.request.user,
            status='booked',
            paid=False
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanPayTicket])
    def pay(self, request, pk=None):
        ticket = self.get_object()
        ticket.paid = True
        ticket.status = 'paid'
        ticket.save()
        return Response(self.get_serializer(ticket).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def cancel(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status == 'cancelled':
            return Response({"detail": "Ticket already cancelled"}, status=status.HTTP_400_BAD_REQUEST)
        ticket.status = 'cancelled'
        ticket.save()
        return Response({"detail": "Ticket cancelled successfully"}, status=status.HTTP_200_OK)