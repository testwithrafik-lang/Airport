import stripe 
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from flights.models import Order
from .models import Payment
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request, order_id):
    try: 
        order = Order.objects.get(id=order_id)
        if order.status.upper() != "PENDING":
            return JsonResponse({"error": "This order is already paid or cancelled"}, status=400)

       
        frontend_url = settings.FRONTEND_URL
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd", 
                    "product_data": {
                        "name": f"Flight Ticket (Order #{order.id})",
                    },
                    "unit_amount": int(order.total_amount * 100), 
                },
                "quantity": 1,
            }],
            mode="payment",
            metadata={"order_id": str(order.id)}, 
          
            success_url=f"{frontend_url}/orders/success/",
            cancel_url=f"{frontend_url}/orders/cancel/"
        )
        
        Payment.objects.create(
            order=order,
            session_url=session.url,
            session_id=session.id,
            money_to_pay=order.total_amount,
            status="PENDING"  
        )

        return JsonResponse({"checkout_url": session.url})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500) 
    
class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.get(id=pk, user=request.user)

            if order.status != Order.Status.PAID:
                return Response({"error": "Only paid orders can be cancelled"}, status=400)

            payment = Payment.objects.filter(order=order).order_by('-id').first()
            if not payment:
                return Response({"error": "Payment info not found"}, status=404)

            stripe.Refund.create(
                payment_intent=payment.session_id
            )

            order.status = Order.Status.CANCELED
            order.save()

            payment.status = Payment.StatusChoices.CANCELED
            payment.save()

            return Response({"message": "Order cancelled and refund processed"})
            
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        except Payment.DoesNotExist:
            return Response({"error": "Payment info not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return HttpResponse(content=str(e), status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")
        payment_intent = session.get("payment_intent")
        if order_id:
            Order.objects.filter(id=order_id).update(status=Order.Status.PAID)
            Payment.objects.filter(session_id=session.id).update(status=Payment.StatusChoices.PAID, session_id=payment_intent)

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")
        if order_id:
            Order.objects.filter(id=order_id).update(status=Order.Status.EXPIRED)
            Payment.objects.filter(session_id=session.id).update(status=Payment.StatusChoices.EXPIRED)

    elif event["type"] == "charge.refunded":
        charge = event["data"]["object"]
        payment = Payment.objects.filter(session_id=charge.get("payment_intent")).first()
        if payment:
            payment.order.status = Order.Status.CANCELED
            payment.order.save()
            payment.status = Payment.StatusChoices.CANCELED
            payment.save()

    return HttpResponse(status=200)