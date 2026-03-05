from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import User
from locations.models import Country, Airport
from fleet.models import Airline, Airplane
from flights.models import Flight, Order, Ticket


class BaseFlightsSetupMixin:
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(email="user@test.com", password="pass1234")
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="pass1234",
            role=User.Roles.ADMIN,
            is_staff=True,
        )

        self.country = Country.objects.create(name="Ukraine", code="UA")
        self.airport_from = Airport.objects.create(
            name="From Airport",
            code="FRM",
            city="City A",
            country=self.country,
        )
        self.airport_to = Airport.objects.create(
            name="To Airport",
            code="TOO",
            city="City B",
            country=self.country,
        )

        self.airline = Airline.objects.create(name="Test Air", code="TA", country="Ukraine")
        self.airplane = Airplane.objects.create(
            airline=self.airline,
            model="A320",
            capacity=180,
            rows=30,
            seats_in_row=6,
            registration_number="UR-TEST",
        )

        self.flight = Flight.objects.create(
            flight_number="TA100",
            airplane=self.airplane,
            departure_airport=self.airport_from,
            arrival_airport=self.airport_to,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=2),
            base_price=100,
        )


class OrderModelTests(BaseFlightsSetupMixin, TestCase):
    def test_reserved_until_and_if_expired(self):
        order = Order.objects.create(user=self.user, currency="USD")
        self.assertIsNotNone(order.reserved_until)
        self.assertEqual(order.status, Order.Status.PENDING)

        order.reserved_until = timezone.now() - timedelta(minutes=1)
        order.save(update_fields=["reserved_until"])
        self.assertTrue(order.if_expired())
        order.expire()
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.EXPIRED)

    def test_cancel_changes_status_and_blocks_for_confirmed(self):
        order = Order.objects.create(user=self.user, currency="USD")
        order.cancel()
        self.assertEqual(order.status, Order.Status.CANCELED)

        confirmed = Order.objects.create(user=self.user, currency="USD", status=Order.Status.CONFIRMED)
        with self.assertRaises(ValueError):
            confirmed.cancel()


class TicketModelTests(BaseFlightsSetupMixin, TestCase):
    def test_seat_number_normalized_and_price_calculated(self):
        order = Order.objects.create(user=self.user, currency="USD")
        ticket = Ticket.objects.create(
            order=order,
            flight=self.flight,
            seat_number=" 12a ",
            ticket_class=Ticket.Class.STANDARD,
        )
        self.assertEqual(ticket.seat_number, "12A")
        self.assertEqual(ticket.price, self.flight.base_price * 1.5)

    def test_cannot_double_book_same_seat_for_active_orders(self):
        order1 = Order.objects.create(user=self.user, currency="USD", status=Order.Status.PAID)
        Ticket.objects.create(
            order=order1,
            flight=self.flight,
            seat_number="12A",
            ticket_class=Ticket.Class.ECONOMY,
        )

        order2 = Order.objects.create(user=self.user, currency="USD", status=Order.Status.PENDING)
        with self.assertRaises(ValueError):
            Ticket.objects.create(
                order=order2,
                flight=self.flight,
                seat_number="12a",
                ticket_class=Ticket.Class.ECONOMY,
            )

class FlightViewSetTests(BaseFlightsSetupMixin, TestCase):
    def test_tickets_available_counts_only_active_orders(self):
        pending = Order.objects.create(user=self.user, currency="USD", status=Order.Status.PENDING)
        paid = Order.objects.create(user=self.user, currency="USD", status=Order.Status.PAID)
        canceled = Order.objects.create(user=self.user, currency="USD", status=Order.Status.CANCELED)

        Ticket.objects.create(order=pending, flight=self.flight, seat_number="1A", ticket_class=Ticket.Class.ECONOMY)
        Ticket.objects.create(order=paid, flight=self.flight, seat_number="1B", ticket_class=Ticket.Class.ECONOMY)
        Ticket.objects.create(order=canceled, flight=self.flight, seat_number="1C", ticket_class=Ticket.Class.ECONOMY)

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/flights/flights/")
        self.assertEqual(response.status_code, 200)
        flight_data = response.data[0]

        total_seats = self.airplane.rows * self.airplane.seats_in_row
        expected_available = total_seats - 2
        self.assertEqual(flight_data["tickets_available"], expected_available)


class OrderViewSetTests(BaseFlightsSetupMixin, TestCase):
    def test_cannot_pay_expired_order(self):
        order = Order.objects.create(
            user=self.user,
            currency="USD",
            status=Order.Status.PENDING,
            reserved_until=timezone.now() - timedelta(minutes=1),
        )
        self.client.force_authenticate(user=self.user)
        url = f"/api/flights/orders/{order.id}/pay/"

        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Reservation expired", response.data["detail"])

    def test_confirm_only_for_admin_and_paid_order(self):
        order = Order.objects.create(user=self.user, currency="USD", status=Order.Status.PAID)

        self.client.force_authenticate(user=self.user)
        url = f"/api/flights/orders/{order.id}/confirm/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
