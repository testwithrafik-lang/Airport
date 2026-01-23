from django.urls import path, include
from rest_framework.routers import DefaultRouter
from flights.views import FlightViewSet

router = DefaultRouter()
router.register(r'', FlightViewSet, basename='flight')

urlpatterns = [
    path('', include(router.urls)),
]
