import stripe
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Flight, Ticket, Order
from .serializers import FlightSerializer, TicketListSerializer, TicketDetailSerializer, OrderSerializer
from users.permissions import IsAdmin


stripe.api_key = settings.STRIPE_SECRET_KEY

class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    def get_permissions(self):
        if self.action in ['create','update','partial_update','destroy']:
            return [IsAdmin()]
        return [IsAuthenticatedOrReadOnly()]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('tickets__flight')
    serializer_class = OrderSerializer
    http_method_names = ['get','post','patch','head','options']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user,'role',None) == 'ADMIN':
            return self.queryset
        return self.queryset.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()
        
        if order.if_expired():
            order.expire()
            return Response({"detail":"Reservation expired. Create new order."}, status=status.HTTP_400_BAD_REQUEST)
        
        if order.status != Order.Status.PENDING:
            return Response({"detail":"Order cannot be paid."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': order.currency,
                        'product_data': {'name': f'Order #{order.id}'},
                        'unit_amount': int(order.total_amount * 100), 
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=settings.FRONTEND_URL + '/success/',
                cancel_url=settings.FRONTEND_URL + '/cancel/',
            )
        
            return Response({'checkout_url': checkout_session.url}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        order = self.get_object()
        if order.status != Order.Status.PAID:
            return Response({"detail":"Only PAID orders can be confirmed."}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.CONFIRMED
        order.save()
        return Response({"detail":"Order confirmed."})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in [Order.Status.CANCELED, Order.Status.CONFIRMED]:
            return Response({"detail":"Cannot cancel this order."}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.CANCELED
        order.save()
        return Response({"detail":"Order canceled successfully."})

class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ticket.objects.select_related('order','flight')
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user,'role',None) == 'ADMIN':
            return self.queryset
        return self.queryset.filter(order__user=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        return TicketDetailSerializer
    
    def get_permissions(self):
        return [IsAuthenticated()]