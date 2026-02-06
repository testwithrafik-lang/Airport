from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CountryAPIView, AirportViewSet

router = DefaultRouter()
router.register(r'airports', AirportViewSet, basename='airport')

urlpatterns = [
  
    path('countries/', CountryAPIView.as_view(), name='country-list'),
    path('countries/<int:pk>/', CountryAPIView.as_view(), name='country-detail'),
    path('', include(router.urls)),
]