from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import User
from flights.models import Order
from payments.models import Payment
from payments import views as payment_views


class BasePaymentsSetupMixin:
    def setUp(self):
        self.client = APIClient()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(email="user@test.com", password="pass1234")
        self.client.force_authenticate(user=self.user)

        self.order = Order.objects.create(
            user=self.user,
            currency="USD",
            total_amount=100,
            status=Order.Status.PENDING,
            reserved_until=timezone.now() + timedelta(minutes=10),
        )


class CreateCheckoutSessionTests(BasePaymentsSetupMixin, TestCase):
    @patch("payments.views.stripe.checkout.Session.create")
    def test_create_checkout_session_creates_payment_and_returns_url(self, mock_create):
        mock_create.return_value.id = "sess_123"
        mock_create.return_value.url = "https://stripe.test/checkout/sess_123"

        url = reverse("create-checkout-session", kwargs={"order_id": self.order.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("checkout_url", data)
        self.assertEqual(data["checkout_url"], "https://stripe.test/checkout/sess_123")

        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, Payment.StatusChoices.PENDING)
        self.assertEqual(payment.money_to_pay, self.order.total_amount)

    def test_cannot_create_checkout_session_for_non_pending_order(self):
        self.order.status = Order.Status.PAID
        self.order.save(update_fields=["status"])

        url = reverse("create-checkout-session", kwargs={"order_id": self.order.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())


class StripeWebhookTests(BasePaymentsSetupMixin, TestCase):
    @patch("payments.views.stripe.Webhook.construct_event")
    def test_checkout_session_completed_marks_order_and_payment_paid(self, mock_construct):
        Payment.objects.create(
            order=self.order,
            session_url="https://stripe.test/checkout/sess_123",
            session_id="sess_123",
            money_to_pay=self.order.total_amount,
            status=Payment.StatusChoices.PENDING,
        )

        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "sess_123",
                    "payment_intent": "pi_123",
                    "metadata": {"order_id": str(self.order.id)},
                }
            },
        }
        mock_construct.return_value = event

        request = self.factory.post(
            reverse("stripe-webhook"),
            data=b"{}",
            content_type="application/json",
        )
        request.headers = {"Stripe-Signature": "test-signature"}

        response = payment_views.stripe_webhook(request)
        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(payment.status, Payment.StatusChoices.PAID)
        self.assertEqual(payment.session_id, "pi_123")

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_checkout_session_expired_marks_order_and_payment_expired(self, mock_construct):
        Payment.objects.create(
            order=self.order,
            session_url="https://stripe.test/checkout/sess_123",
            session_id="sess_123",
            money_to_pay=self.order.total_amount,
            status=Payment.StatusChoices.PENDING,
        )

        event = {
            "type": "checkout.session.expired",
            "data": {"object": {"id": "sess_123", "metadata": {"order_id": str(self.order.id)}}},
        }
        mock_construct.return_value = event

        request = self.factory.post(
            reverse("stripe-webhook"),
            data=b"{}",
            content_type="application/json",
        )
        request.headers = {"Stripe-Signature": "test-signature"}

        response = payment_views.stripe_webhook(request)
        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(self.order.status, Order.Status.EXPIRED)
        self.assertEqual(payment.status, Payment.StatusChoices.EXPIRED)


class CancelOrderViewTests(BasePaymentsSetupMixin, TestCase):
    @patch("payments.views.stripe.Refund.create")
    def test_cancel_paid_order_refunds_and_sets_statuses(self, mock_refund):
        self.order.status = Order.Status.PAID
        self.order.save(update_fields=["status"])

        payment = Payment.objects.create(
            order=self.order,
            session_url="https://stripe.test/checkout/sess_123",
            session_id="pi_123",
            money_to_pay=self.order.total_amount,
            status=Payment.StatusChoices.PAID,
        )

        url = reverse("order-cancel", kwargs={"pk": self.order.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELED)
        self.assertEqual(payment.status, Payment.StatusChoices.CANCELED)
        mock_refund.assert_called_once_with(payment_intent=payment.session_id)

    def test_cancel_order_requires_paid_status(self):
        url = reverse("order-cancel", kwargs={"pk": self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only paid orders can be cancelled", response.data["error"])
