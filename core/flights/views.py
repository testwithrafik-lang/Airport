import stripe
from django.conf import settings
from django.db.models import Count, F, Q
from django.core.mail import send_mail  
from rest_framework import viewsets, status
from rest_framework.decorators import action 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Flight, Ticket, Order
from .serializers import FlightSerializer, OrderSerializer, TicketListSerializer, TicketDetailSerializer
from users.permissions import IsAdmin

stripe.api_key = settings.STRIPE_SECRET_KEY

class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.select_related("airplane", "departure_airport", "arrival_airport").all()    
    serializer_class = FlightSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.annotate(
                tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row") - 
                    Count("tickets", filter=Q(tickets__order__status__in=["PAID", "PENDING", "CONFIRMED"]))
                )
            )
        return queryset.order_by("id")

    def get_permissions(self):
        if self.action in ['create','update','partial_update','destroy']:
            return [IsAdmin()]
        return [IsAuthenticatedOrReadOnly()]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('tickets__flight').all()
    serializer_class = OrderSerializer
    http_method_names = ['get','post','patch','head','options']

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        if user.is_staff or getattr(user,'role',None) == 'ADMIN':
            return self.queryset
        return self.queryset.filter(user=user)
    
    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user) 
        self.send_order_email(order, "order_created")

    def get_permissions(self):
        return [IsAuthenticated()]

    def send_order_email(self, order, email_type):

        user_email = order.user.email
        subject = ""
        message = ""

        if email_type == "order_created":
            subject = f"Order #{order.id} Created - Airport Service"
            message = (
                f"Your order #{order.id} has been created and is pending payment.\n"
                f"Total amount: {order.total_amount} {order.currency}\n"
                f"Please complete the payment within the reservation time limit."
            )
        
        elif email_type == "payment_success":
            subject = f"Payment Received: Order #{order.id}"
            message = (
                f"Payment for order #{order.id} was successful!\n"
                f"Status: PAID. Our staff will confirm your booking shortly."
            )

        elif email_type == "order_confirmed":
            subject = f"Booking Confirmed: Order #{order.id}"
            tickets_info = "\n".join([
                f"- Flight {t.flight.flight_number}: Row {t.row}, Seat {t.seat}" 
                for t in order.tickets.all()
            ])
            message = (
                f"Great news! Your booking for order #{order.id} is officially confirmed.\n"
                f"Your tickets:\n{tickets_info}\n\n"
                f"Thank you for choosing Airport Service!"
            )

        elif email_type == "order_cancelled":
            subject = f"Order #{order.id} Cancelled"
            message = (
                f"Order #{order.id} has been cancelled.\n"
                f"If a refund is applicable, it will be processed according to our policy."
            )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()
        order.refresh_from_db()

        if order.if_expired():
            order.expire()
            return Response({"detail":"Reservation expired. Create new order."}, status=status.HTTP_400_BAD_REQUEST)
    
        if order.status != Order.Status.PENDING:
            return Response({"detail": "Order cannot be paid."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": order.currency,
                            "product_data": {"name": f"Order #{order.id}"},
                            "unit_amount": int(order.total_amount * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                metadata={"order_id": str(order.id)},
                success_url=f"{settings.FRONTEND_URL}/success",
                cancel_url=f"{settings.FRONTEND_URL}/cancel",
            )

            from payments.models import Payment

            Payment.objects.create(
                order=order,
                session_id=checkout_session.id,
                session_url=checkout_session.url,
                money_to_pay=order.total_amount,
                status=Payment.StatusChoices.PENDING,
            )

            return Response({"checkout_url": checkout_session.url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        order = self.get_object()
        if order.status != Order.Status.PAID:
            return Response({"detail":"Only PAID orders can be confirmed."}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.CONFIRMED
        order.save()
        self.send_order_email(order, "order_confirmed")
        return Response({"detail":"Order confirmed."})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in [Order.Status.CANCELED, Order.Status.EXPIRED]:
            return Response({"detail":"Order is already canceled or expired."}, status=status.HTTP_400_BAD_REQUEST)
        refund_percent = order.get_refund_percentage()

        if order.status in [Order.Status.PAID, Order.Status.CONFIRMED]:
            if refund_percent > 0:
                message = f"Order canceled. Refund available: {refund_percent}% (use payments cancel endpoint to process)."
            else:
                message = "Order canceled. No refund possible (less than 1 hour to departure)."
        else:
            message = "Order canceled successfully."

        order.status = Order.Status.CANCELED
        order.save()
        self.send_order_email(order, "order_cancelled")
        return Response({"detail": message}, status=status.HTTP_200_OK)

class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ticket.objects.select_related('order', 'flight').all()
    
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