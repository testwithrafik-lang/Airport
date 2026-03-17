import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from flights.models import Order
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def _send_order_email(order: Order, email_type: str) -> None:
    user_email = order.user.email
    subject = ""
    message = ""

    if email_type == "payment_success":
        subject = f"Payment Received: Order #{order.id}"
        message = (
            f"Payment for order #{order.id} was successful!\n"
            f"Total amount: {order.total_amount} {order.currency}\n"
            f"Status: PAID."
        )
    elif email_type == "order_cancelled":
        subject = f"Order #{order.id} Cancelled"
        message = (
            f"Order #{order.id} has been cancelled.\n"
            f"If a refund is applicable, it will be processed according to our policy."
        )
    elif email_type == "order_expired":
        subject = f"Order #{order.id} Expired"
        message = (
            f"Your reservation for order #{order.id} has expired.\n"
            f"Please create a new order if you still want to book."
        )
    elif email_type == "order_refunded":
        subject = f"Refund Processed: Order #{order.id}"
        message = (
            f"Refund for order #{order.id} has been processed.\n"
            f"Status: REFUNDED."
        )
    else:
        return

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )


def create_checkout_session(request, order_id):
    try:
        order = Order.objects.get(id=order_id)

        if order.status != Order.Status.PENDING:
            return JsonResponse({"error": "Order already processed"}, status=400)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Flight ticket order {order.id}",
                        },
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

        Payment.objects.create(
            order=order,
            session_id=session.id,
            session_url=session.url,
            money_to_pay=order.total_amount,
            status=Payment.StatusChoices.PENDING,
        )

        return JsonResponse({"checkout_url": session.url})

    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)


class RefundOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)

            if order.status != Order.Status.PAID:
                return Response(
                    {"error": "Only paid orders can be refunded"}, status=400
                )

            payment = Payment.objects.filter(order=order).first()
            if not payment:
                return Response(
                    {"error": "Payment record not found"}, status=404
                )

            session = stripe.checkout.Session.retrieve(payment.session_id)

            stripe.Refund.create(
                payment_intent=session.payment_intent,
            )

            return Response({"message": "Refund requested"})

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except Exception:
        return HttpResponse(status=400)

    event_type = event.get("type")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")

        if not order_id:
            return HttpResponse(status=200)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return HttpResponse(status=404)

        if order.status != Order.Status.PAID:
            order.status = Order.Status.PAID
            order.save()

        Payment.objects.filter(session_id=session.get("id")).update(
            status=Payment.StatusChoices.PAID
        )
        _send_order_email(order, "payment_success")

    elif event_type == "checkout.session.expired":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")

        if not order_id:
            return HttpResponse(status=200)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return HttpResponse(status=404)

        if order.status == Order.Status.PENDING:
            order.status = Order.Status.EXPIRED
            order.save()

        Payment.objects.filter(session_id=session.get("id")).update(
            status=Payment.StatusChoices.EXPIRED
        )
        _send_order_email(order, "order_expired")

    elif event_type == "payment_intent.canceled":
        pi = event["data"]["object"]
        payment_intent = pi.get("id")

        if payment_intent:
            sessions = stripe.checkout.Session.list(
                payment_intent=payment_intent
            ).data
            if sessions:
                session = sessions[0]
                metadata = getattr(session, "metadata", None) or {}
                order_id = metadata.get("order_id")

                if order_id:
                    try:
                        order = Order.objects.get(id=order_id)
                    except Order.DoesNotExist:
                        return HttpResponse(status=404)

                    if order.status == Order.Status.PENDING:
                        order.status = Order.Status.CANCELED
                        order.save()

                    Payment.objects.filter(
                        session_id=getattr(session, "id", None)
                    ).update(status=Payment.StatusChoices.CANCELED)
                    _send_order_email(order, "order_cancelled")

    elif event_type == "charge.refunded":
        charge = event["data"]["object"]
        payment_intent = charge.get("payment_intent")

        if payment_intent:
            sessions = stripe.checkout.Session.list(
                payment_intent=payment_intent
            ).data
            if sessions:
                session_id = sessions[0].id
                payment = Payment.objects.filter(
                    session_id=session_id
                ).first()
                if payment:
                    order = payment.order
                    if order.status != Order.Status.REFUNDED:
                        order.status = Order.Status.REFUNDED
                        order.save()

                    _send_order_email(order, "order_refunded")

    return HttpResponse(status=200)