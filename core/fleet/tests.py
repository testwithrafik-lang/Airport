from django.test import TestCase
from django.db.utils import IntegrityError
from rest_framework.exceptions import ValidationError
from .models import Airline, Airplane
from .serializers import AirplaneSerializer

class FleetAdvancedTests(TestCase):
    def setUp(self):
        self.airline = Airline.objects.create(
            name="SkyUp", 
            code="SQY", 
            country="Ukraine"
        )

    def test_unique_airline_code(self):
        with self.assertRaises(IntegrityError):
            Airline.objects.create(name="Another", code="SQY", country="Ukraine")

    def test_airplane_math_logic(self):
        airplane = Airplane.objects.create(
            airline=self.airline,
            model="Boeing 737",
            capacity=180,
            rows=30,
            seats_in_row=6,
            registration_number="UR-SQY"
        )
        self.assertEqual(airplane.rows * airplane.seats_in_row, airplane.capacity)

    def test_airplane_serializer_validation(self):
        bad_data = {
            "airline": self.airline.id,
            "model": "Boeing",
            "capacity": -10,
            "registration_number": "UR-BAD",
            "rows": 20,
            "seats_in_row": 6
        }
        serializer = AirplaneSerializer(data=bad_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('capacity', serializer.errors)

    def test_airplane_str_representation(self):
        airplane = Airplane.objects.create(
            airline=self.airline,
            model="Airbus A320",
            capacity=150,
            rows=25,
            seats_in_row=6,
            registration_number="UR-ABC"
        )
        self.assertEqual(str(airplane), "Airbus A320 (UR-ABC)")