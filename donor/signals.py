from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_donor_profile(sender, instance, created, **kwargs):
    """Auto-create donor profile when donor user is created"""
    if created and instance.user_type == 'DONOR':
        from .models import DonorProfile
        DonorProfile.objects.create(user=instance)
