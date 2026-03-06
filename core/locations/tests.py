from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse

from locations.models import Country, Airport


class CountryModelTests(TestCase):
    def test_str_returns_name(self):
        country = Country.objects.create(name="Ukraine", code="UA")
        self.assertEqual(str(country), "Ukraine")


class AirportModelTests(TestCase):
    def test_str_returns_name_and_code(self):
        country = Country.objects.create(name="Ukraine", code="UA")
        airport = Airport.objects.create(
            name="Boryspil",
            code="KBP",
            city="Kyiv",
            country=country,
        )
        self.assertEqual(str(airport), "Boryspil (KBP)")


class CountryAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.country = Country.objects.create(name="Ukraine", code="UA")

    def test_get_country_list(self):
        response = self.client.get("/api/locations/countries/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_country_detail(self):
        url = f"/api/locations/countries/{self.country.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], self.country.name)


class AirportViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.country = Country.objects.create(name="Ukraine", code="UA")
        self.airport = Airport.objects.create(
            name="Boryspil",
            code="KBP",
            city="Kyiv",
            country=self.country,
        )

    def test_list_airports(self):
        response = self.client.get("/api/locations/airports/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
