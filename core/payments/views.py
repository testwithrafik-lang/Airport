import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from flights.models import Order
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(request, order_id):
    try:
        order = Order.objects.get(id=order_id)

        if order.status != Order.Status.PENDING:
            return JsonResponse({"error": "Order already processed"}, status=400)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Flight ticket order {order.id}",
                    },
                    "unit_amount": int(order.total_amount * 100),
                },
                "quantity": 1,
            }],
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
            status="PENDING"
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
                return Response({"error": "Only paid orders can be refunded"}, status=400)

            payment = Payment.objects.filter(order=order).first()
            if not payment:
                return Response({"error": "Payment record not found"}, status=404)

            session = stripe.checkout.Session.retrieve(payment.session_id)

           
            stripe.Refund.create(
                payment_intent=session.payment_intent
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
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session["metadata"]["order_id"]
        
        try:
            order = Order.objects.get(id=order_id)
            order.status = "PAID"
            order.save()
            
            Payment.objects.filter(session_id=session["id"]).update(status="PAID")
        except Order.DoesNotExist:
            return HttpResponse(status=404)

    if event["type"] == "charge.refunded":
        charge = event["data"]["object"]
        payment_intent = charge["payment_intent"]
        sessions = stripe.checkout.Session.list(payment_intent=payment_intent).data
        if sessions:
            session_id = sessions[0].id
            payment = Payment.objects.filter(session_id=session_id).first()
            if payment:
                order = payment.order
                order.status = "REFUNDED"
                order.save()
                Payment.objects.filter(id=payment.id).update(status="REFUNDED")

    return HttpResponse(status=200)