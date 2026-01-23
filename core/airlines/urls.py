from django.urls import path
from airlines.views import AirlineViewSet

airline_list = AirlineViewSet.as_view({'get': 'list'})
airline_detail = AirlineViewSet.as_view({'get': 'retrieve'})

urlpatterns = [
    path('', airline_list, name='airline-list'),
    path('<int:pk>/', airline_detail, name='airline-detail'),
]

