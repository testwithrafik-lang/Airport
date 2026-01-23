from django.urls import path
from tickets.views import TicketViewSet

ticket_list = TicketViewSet.as_view({'get': 'list'})
ticket_detail = TicketViewSet.as_view({'get': 'retrieve'})

urlpatterns = [
    path('', ticket_list, name='ticket-list'),
    path('<int:pk>/', ticket_detail, name='ticket-detail'),
]
