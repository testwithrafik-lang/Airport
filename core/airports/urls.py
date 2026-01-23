from django.urls import path
from airports.views import AirportViewSet

airport_list = AirportViewSet.as_view({'get': 'list'})
airport_detail = AirportViewSet.as_view({'get': 'retrieve'})

urlpatterns = [
    path('', airport_list, name='airport-list'),
    path('<int:pk>/', airport_detail, name='airport-detail'),
]
