from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AirlineViewSet, AirplaneViewSet

router = DefaultRouter()
router.register(r'airlines', AirlineViewSet, basename='airline')
router.register(r'airplanes', AirplaneViewSet, basename='airplane')

urlpatterns = [
    path('', include(router.urls)),
]