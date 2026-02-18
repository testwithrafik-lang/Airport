import stripe 
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from flights.models import Order
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request, order_id):
    try: 
        order = Order.objects.get(id=order_id)
        if order.status.upper() != "PENDING":
            return JsonResponse({"error": "This order is already paid or cancelled"}, status=400)

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
            success_url="http://localhost:8000/api/flights/orders/", 
            cancel_url="http://localhost:8000/api/flights/orders/", 
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
        order_id = session["metadata"]["order_id"]

      
        Order.objects.filter(id=order_id).update(status="PAID")
        Payment.objects.filter(session_id=session.id).update(status="PAID")
        print(f"Order {order_id} successfully paid!")

    return HttpResponse(status=200)