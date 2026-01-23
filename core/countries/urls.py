from django.urls import path, include
from rest_framework.routers import DefaultRouter
from countries.views import CountryViewSet

router = DefaultRouter()
router.register(r'', CountryViewSet, basename='country')

urlpatterns = [
    path('', include(router.urls)),
]

