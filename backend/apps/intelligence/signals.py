from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.resources.models import Resource
from .services.automatic_matching import schedule_matching

@receiver(post_save, sender=Resource)
def match_after_surplus_commit(sender, instance, **kwargs):
    schedule_matching(instance, getattr(instance, 'created_by', None))
