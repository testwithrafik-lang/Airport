from django.urls import path
from flights.views import FlightAPIView

urlpatterns = [
    path('', FlightAPIView.as_view(), name='flight-list'),
    path('<int:pk>/', FlightAPIView.as_view(), name='flight-detail'),
]
