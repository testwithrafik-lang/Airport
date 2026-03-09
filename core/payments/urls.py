from django.urls import path
from .views import create_checkout_session, stripe_webhook, RefundOrderView

urlpatterns = [
    path('create-checkout-session/<int:order_id>/', create_checkout_session, name='create_checkout_session'),
    path('webhook/', stripe_webhook, name='stripe_webhook'),
    path('orders/<int:pk>/cancel/', RefundOrderView.as_view(), name='cancel_order'),
]