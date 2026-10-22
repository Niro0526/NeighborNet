"""Individual food rescue; organization and disaster requisitions remain independent."""
import uuid
from django.conf import settings
from django.db import models


class PersonalLocation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)


class FoodClaim(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Awaiting coordinator approval'
        APPROVED = 'APPROVED', 'Approved'
        ASSIGNED = 'ASSIGNED', 'Volunteer assigned'
        PICKED_UP = 'PICKED_UP', 'Picked up'
        DELIVERED = 'DELIVERED', 'Delivered'
        RECEIVED = 'RECEIVED', 'Receipt confirmed'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource = models.ForeignKey('resources.Resource', on_delete=models.PROTECT, related_name='personal_claims')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='food_claims')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    method = models.CharField(max_length=10, choices=[('delivery', 'Volunteer delivery'), ('pickup', 'Authorized pickup')])
    address = models.CharField(max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name='approved_food_claims')
    pickup_code = models.CharField(max_length=12, blank=True, default='')
    volunteer = models.ForeignKey('volunteers.Volunteer', on_delete=models.PROTECT, null=True, blank=True, related_name='food_claims')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='positive_personal_claim_quantity'),
            models.UniqueConstraint(fields=['resource', 'recipient'], condition=~models.Q(status__in=['REJECTED', 'CANCELLED']), name='unique_active_personal_food_claim'),
        ]


class FoodClaimEvent(models.Model):
    claim = models.ForeignKey(FoodClaim, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=20, choices=FoodClaim.Status.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
