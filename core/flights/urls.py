from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FlightViewSet, TicketViewSet

router = DefaultRouter()
router.register(r'flights', FlightViewSet, basename='flight')
router.register(r'tickets', TicketViewSet, basename='ticket')

urlpatterns = [path('', include(router.urls)),]