"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from users.views import UserViewSet
from countries.views import CountryViewSet
from airports.views import AirportViewSet
from airlines.views import AirlineViewSet
from airplanes.views import AirplaneViewSet
from flights.views import FlightViewSet
from tickets.views import TicketViewSet


router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register(r'countries', CountryViewSet, basename='country')
router.register(r'airports', AirportViewSet, basename='airport')
router.register(r'airlines', AirlineViewSet, basename='airline')
router.register(r'airplanes', AirplaneViewSet, basename='airplane')
router.register(r'flights', FlightViewSet, basename='flight')
router.register(r'tickets', TicketViewSet, basename='ticket')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/',SpectacularSwaggerView.as_view(url_name='schema'),name='swagger-ui'),
    path('api/', include(router.urls)),
]