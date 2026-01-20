from rest_framework.routers import DefaultRouter
from .views import AirlineViewSet

router = DefaultRouter()
router.register(r'airlines', AirlineViewSet, basename='airline')

urlpatterns = router.urls
