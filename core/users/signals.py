from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import User

@receiver(pre_save, sender=User)
def security_notifications(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    if old_user.phone != instance.phone:
        send_mail(
            "Security Update: Phone number changed",
            f"Your phone number has been updated from {old_user.phone} to {instance.phone}.",
            None,
            [instance.email]
        )

    if old_user.password != instance.password:
        send_mail(
            "Security Alert: Password changed",
            "Your password has been successfully changed. If you did not perform this action, please contact support immediately.",
            None,
            [instance.email]
        )