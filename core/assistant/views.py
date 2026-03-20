from datetime import timedelta
import google.generativeai as genai
import re
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from fleet.models import Airplane
from flights.models import Flight, Order
from locations.models import Country
from payments.models import Payment
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

PROJECT_KEYWORDS = {
    "flight",
    "flights",
    "order",
    "orders",
    "ticket",
    "tickets",
    "airplane",
    "airplanes",
    "planes",
    "plane",
    "country",
    "countries",
    "airport",
    "stripe",
    "webhook",
    "payment",
    "payments",
    "refund",
    "cancel",
    "canceled",
    "refunded",
    "email",
    "mail",
    "api",
    "swagger",
    "endpoint",
    "/api/",
    "404",
    "pending",
    "paid",
    "django",
    "database",
    "table",
    "model",
    "migration",
    "server",
    "logs",
}

def _is_project_question(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in PROJECT_KEYWORDS)

def _get_tomorrow_flights():
    tomorrow = (timezone.now() + timedelta(days=1)).date()
    return _get_flights_for_date(tomorrow)

def _get_flights_for_date(target_date):
    qs = (
        Flight.objects.filter(departure_time__date=target_date)
        .select_related("departure_airport", "arrival_airport")
        .order_by("departure_time")
    )
    flights = []
    for f in qs:
        flights.append(
            {
                "id": f.id,
                "flight_number": f.flight_number,
                "departure_airport": f.departure_airport.code,
                "arrival_airport": f.arrival_airport.code,
                "departure_time": f.departure_time,
                "arrival_time": f.arrival_time,
                "status": f.status,
            }
        )
    return flights

def _get_airplanes_answer():
    planes_qs = Airplane.objects.select_related("airline").order_by("model", "registration_number")
    planes = list(planes_qs)
    if not planes:
        return "There is currently no airplane data in the database."

    lines = []
    for p in planes:
        lines.append(
            f"{p.model} ({p.registration_number}) — {p.airline.name}, "
            f"{p.capacity} seats; {p.rows} rows x {p.seats_in_row} seats per row"
        )
    return "Here are the airplanes in the system:\n" + "\n".join([f"• {l}" for l in lines])

def _get_countries_answer():
    countries = list(Country.objects.all().order_by("name"))
    if not countries:
        return "There are currently no countries in the database."
    return "List of countries:\n" + "\n".join([f"• {c.name}" for c in countries])

def _get_countries_with_flights_answer():
    flights = (
        Flight.objects.select_related(
            "departure_airport__country", "arrival_airport__country"
        ).all()
    )
    countries = set()
    for f in flights:
        if f.departure_airport and f.departure_airport.country:
            countries.add(f.departure_airport.country.name)
        if f.arrival_airport and f.arrival_airport.country:
            countries.add(f.arrival_airport.country.name)

    if not countries:
        return "I don't see any flights in the system to list the countries."

    sorted_c = sorted(countries)
    return "Countries with flights (departure or arrival):\n" + "\n".join([f"• {c}" for c in sorted_c])

def _get_orders_with_payment_for_date(target_date):
    orders = (
        Order.objects.filter(created_at__date=target_date)
        .order_by("-created_at")
        .prefetch_related("payments")
    )
    out = []
    for o in orders:
        p = o.payments.first()
        out.append(
            {
                "order_id": o.id,
                "order_status": o.status,
                "currency": o.currency,
                "total_amount": str(o.total_amount),
                "payment_status": p.status if p else None,
            }
        )
    return out

def _build_payments_answer(days_ago: int, only: str | None = None):
    target_date = (timezone.now() - timedelta(days=days_ago)).date()
    items = _get_orders_with_payment_for_date(target_date)

    if only:
        if only == "paid":
            items = [x for x in items if x["payment_status"] == "PAID" or x["order_status"] == "PAID"]
        elif only == "canceled":
            items = [x for x in items if x["payment_status"] == "CANCELED" or x["order_status"] == "CANCELED"]
        elif only == "refunded":
            items = [x for x in items if x["payment_status"] == "REFUNDED" or x["order_status"] == "REFUNDED"]

    if not items:
        return f"No {only or 'payments'} found for {days_ago} day(s) ago."

    lines = []
    for x in items:
        pay = x["payment_status"] or "NO_PAYMENT"
        lines.append(
            f"Order #{x['order_id']}: Order={x['order_status']}, Payment={pay}, {x['total_amount']} {x['currency']}"
        )

    title = f"Payments for {days_ago} day(s) ago"
    if only:
        title += f" ({only})"
    return title + ":\n" + "\n".join(lines)

def _parse_days_ago(text: str):
    t = (text or "").lower()
    if "yesterday" in t:
        return 1
    if "day before yesterday" in t:
        return 2
    
    m = re.search(r"(\d+)\s*day[s]?\s*ago", t)
    if m:
        return int(m.group(1))
    return None

class ProjectAssistantAskView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        message = (request.data or {}).get("message") or (request.data or {}).get("text")
        if not message or not isinstance(message, str):
            return Response(
                {"error": "message is required (string)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not _is_project_question(message):
            return Response(
                {
                    "answer": (
                        "Airport-AI: I only answer questions related to this project (flights, orders, Stripe payments, emails).\n"
                        "Examples: 'What flight is tomorrow?' or 'Which airplanes are available?'."
                    )
                }
            )

        lower = message.lower()

        if any(k in lower for k in ["airplane", "planes", "plane"]):
            return Response({"answer": _get_airplanes_answer()})

        if any(k in lower for k in ["country", "countries"]):
            if any(k in lower for k in ["flight", "flights"]):
                return Response({"answer": _get_countries_with_flights_answer()})
            return Response({"answer": _get_countries_answer()})

        if ("tomorrow" in lower) and ("flight" in lower):
            flights = _get_tomorrow_flights()
            if not flights:
                return Response({"answer": "No flights found for tomorrow."})

            lines = [
                f"ID {f['id']}: {f['flight_number']} ({f['departure_airport']} -> {f['arrival_airport']}), "
                f"departure {f['departure_time']}"
                for f in flights
            ]
            return Response({"answer": "Flights for tomorrow:\n" + "\n".join(lines), "flights": flights})

        days_ago = _parse_days_ago(lower)
        if days_ago is not None and ("flight" in lower):
            target_date = (timezone.now() - timedelta(days=days_ago)).date()
            flights = _get_flights_for_date(target_date)
            if not flights:
                return Response({"answer": f"No flights found for {days_ago} day(s) ago."})

            lines = [
                f"ID {f['id']}: {f['flight_number']} ({f['departure_airport']} -> {f['arrival_airport']}), "
                f"departure {f['departure_time']}"
                for f in flights
            ]
            return Response({"answer": f"Flights for {days_ago} day(s) ago:\n" + "\n".join(lines), "flights": flights})

        if any(k in lower for k in ["payment", "stripe", "refund", "cancel", "paid"]):
            payment_days_ago = _parse_days_ago(lower)
            if payment_days_ago is not None:
                only = None
                if "refund" in lower or "refunded" in lower:
                    only = "refunded"
                elif "cancel" in lower or "canceled" in lower:
                    only = "canceled"
                elif "paid" in lower or "success" in lower:
                    only = "paid"
                return Response({"answer": _build_payments_answer(payment_days_ago, only=only)})

        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            return Response(
                {
                    "answer": (
                        "I see your project-related question, but Gemini is not configured (GEMINI_API_KEY is missing). "
                        "I can only answer specific queries using database records (flights/planes/countries/payments)."
                    )
                }
            )

        genai.configure(api_key=api_key)
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_name)

        system_prompt = (
            "You are the Project Assistant for the Airport API service. "
            "Respond ONLY to questions about this project: its API, models (Flight, Order, Ticket, Payment), "
            "Stripe payment logic (webhook, checkout.session.completed, cancel, refund), and email notifications. "
            "If a question is unrelated to this project or you lack sufficient information from the context below, "
            "explain what needs to be clarified or state that there is insufficient data in the system. "
            "Respond in English, in a helpful and human-like manner. "
            "Do not give dry 'I don't know' answers—instead, suggest what to check or what data is needed."
        )

        context = (
            "API endpoints (examples):\n"
            "- POST /api/flights/orders/{id}/pay/\n"
            "- POST /api/payments/create-checkout-session/{order_id}/\n"
            "- POST /api/payments/webhook/ (Stripe webhook)\n\n"
            "Models and Statuses:\n"
            "- Order.status: PENDING, PAID, CANCELED, EXPIRED, CONFIRMED, REFUNDED\n"
            "- Payment.status: PENDING, PAID, CANCELED, EXPIRED, REFUNDED\n\n"
            "Emails:\n"
            "- payment_success -> 'Payment Received: Order #...'\n"
            "- order_cancelled -> 'Order #... Cancelled'\n"
            "- order_refunded -> 'Refund Processed: Order #...'\n"
        )

        full_prompt = f"{system_prompt}\n\nContext:\n{context}\nUser Question:\n{message}\n"
        try:
            resp = model.generate_content(full_prompt)
            text = getattr(resp, "text", None) or str(resp)
            text = (text or "").strip()
            if not text:
                text = "I am sorry, I don't have enough information to answer that."
            return Response({"answer": text})
        except Exception as e:
            return Response(
                {"error": f"Gemini request failed: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

class AirportAiPageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return render(request, "assistant/ai.html")