from django.urls import path
from countries.views import CountryAPIView

urlpatterns = [
    path('', CountryAPIView.as_view(), name='country-list'),
    path('<int:pk>/', CountryAPIView.as_view(), name='country-detail'),
]
