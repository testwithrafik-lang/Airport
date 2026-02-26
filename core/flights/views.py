from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Flight, Ticket, Order
from .serializers import (
    FlightSerializer,
    TicketListSerializer,
    TicketDetailSerializer,
    OrderSerializer,
)
from users.permissions import IsAdmin


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticatedOrReadOnly()]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('tickets__flight')
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', None) == 'ADMIN':
            return self.queryset
        return self.queryset.filter(user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ticket.objects.select_related('order', 'flight')

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', None) == 'ADMIN':
            return self.queryset
        return self.queryset.filter(order__user=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        return TicketDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]