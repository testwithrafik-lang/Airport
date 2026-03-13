from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order

@receiver(post_save, sender=Order)
def send_order_status_notifications(sender, instance, **kwargs):
    if instance.status == "PAID":
        send_mail(
            subject="Order Paid Successfully",
            message=f"Your order #{instance.id} has been paid. Your ticket is now active.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            fail_silently=False,
        )

    elif instance.status == "CANCELED":
        send_mail(
            subject="Order Cancelled",
            message=f"Your order #{instance.id} has been canceled.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            fail_silently=False,
        )