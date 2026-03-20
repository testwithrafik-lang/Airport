from datetime import timedelta

import google.generativeai as genai
from django.conf import settings
from django.utils import timezone
from flights.models import Flight
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


PROJECT_KEYWORDS = {
    # Flights/Orders
    "рейс",
    "flight",
    "orders",
    "order",
    "замов",
    "tickets",
    "ticket",
    # Payments/Stripe/Email
    "stripe",
    "webhook",
    "оплат",
    "payment",
    "refund",
    "cancel",
    "canceled",
    "refunded",
    "лист",
    "email",
    # API/SWAGGER
    "api",
    "swagger",
    "endpoint",
    "/api/",
    "404",
    # Status
    "pending",
    "paid",
    # Django/BД
    "django",
    "база",
    "таблиц",
    "модель",
    "міграц",
    "сервер",
    "лог",
}


def _is_project_question(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in PROJECT_KEYWORDS)


def _get_tomorrow_flights():
    tomorrow = (timezone.now() + timedelta(days=1)).date()
    qs = (
        Flight.objects.filter(departure_time__date=tomorrow)
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


class ProjectAssistantAskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = (request.data or {}).get("message") or (request.data or {}).get("text")
        if not message or not isinstance(message, str):
            return Response(
                {"error": "message is required (string)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Груба фільтрація: не по проекту -> "Не знаю".
        # Це гарантує, що на погоду/емоції він не відповідатиме як чат.
        if not _is_project_question(message):
            return Response({"answer": "Не знаю."})

        lower = message.lower()
        if ("завтра" in lower or "tomorrow" in lower) and ("рейс" in lower or "flight" in lower):
            flights = _get_tomorrow_flights()
            if not flights:
                return Response({"answer": "На завтра рейсів не знайдено."})

            lines = [
                f"ID {f['id']}: {f['flight_number']} ({f['departure_airport']} -> {f['arrival_airport']}), "
                f"відправлення {f['departure_time']}"
                for f in flights
            ]
            return Response({"answer": "На завтра рейси:\n" + "\n".join(lines), "flights": flights})

        # Все інше (тільки по проекту) - беремо відповідь у Gemini,
        # але просимо відповідати "Не знаю" якщо не вистачає контексту.
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            return Response(
                {"error": "GEMINI_API_KEY is not configured in environment (.env)"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        genai.configure(api_key=api_key)
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_name)

        system_prompt = (
            "Ти - Project Assistant для сервісу Airport API. "
            "Відповідай ТІЛЬКИ на питання про цей проект: його API, моделі (Flight/Order/Ticket/Payment), "
            "логіку оплати Stripe (webhook, checkout.session.completed, cancel/refund) і відправку email. "
            "Якщо питання не стосується цього проекту або ти не маєш достатньо інформації з контексту нижче — "
            "виведи рівно: 'Не знаю.' . "
            "Відповідай українською, без привітань та дрібної балаканини."
        )

        context = (
            "API endpoints (приклади):\n"
            "- POST /api/flights/orders/{id}/pay/\n"
            "- POST /api/payments/create-checkout-session/{order_id}/\n"
            "- POST /api/payments/webhook/ (Stripe webhook)\n\n"
            "Моделі та статуси:\n"
            "- Order.status: PENDING, PAID, CANCELED, EXPIRED, CONFIRMED, REFUNDED\n"
            "- Payment.status: PENDING, PAID, CANCELED, EXPIRED, REFUNDED (залежить від коду)\n\n"
            "Листи:\n"
            "- payment_success -> 'Payment Received: Order #...'\n"
            "- order_cancelled -> 'Order #... Cancelled'\n"
            "- order_refunded -> 'Refund Processed: Order #...'\n"
        )

        full_prompt = f"{system_prompt}\n\nКонтекст:\n{context}\nПитання користувача:\n{message}\n"
        try:
            resp = model.generate_content(full_prompt)
            text = getattr(resp, "text", None) or str(resp)
            text = (text or "").strip()
            # Щоб сильніше контролювати формат.
            if not text:
                text = "Не знаю."
            return Response({"answer": text})
        except Exception as e:
            return Response(
                {"error": f"Gemini request failed: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

