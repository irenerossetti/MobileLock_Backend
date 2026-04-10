from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, Usuario


@receiver(post_save, sender=Usuario)
def crear_profile_automatico(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(usuario=instance)


@receiver(post_save, sender=Usuario)
def guardar_profile_existente(sender, instance, **kwargs):
    Profile.objects.get_or_create(usuario=instance)
