from django.urls import path
from airplanes.views import AirplaneViewSet

airplane_list = AirplaneViewSet.as_view({'get': 'list'})
airplane_detail = AirplaneViewSet.as_view({'get': 'retrieve'})

urlpatterns = [
    path('', airplane_list, name='airplane-list'),
    path('<int:pk>/', airplane_detail, name='airplane-detail'),
]
