from rest_framework.routers import DefaultRouter
from .views import FlightViewSet

router = DefaultRouter()
router.register(r'flights', FlightViewSet, basename='flight')

urlpatterns = router.urls
