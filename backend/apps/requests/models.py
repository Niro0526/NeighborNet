import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from common.validators import validate_positive_quantity
from apps.resources.models import ResourceCategoryChoices

class RequestPriorityChoices(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent Emergency'

class RequestStatusChoices(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    PARTIALLY_ALLOCATED = 'PARTIALLY_ALLOCATED', 'Partially Allocated'
    ALLOCATED = 'ALLOCATED', 'Allocated'
    FULFILLED = 'FULFILLED', 'Fulfilled'
    CANCELLED = 'CANCELLED', 'Cancelled'

def generate_request_id():
    return f"REQ-{uuid.uuid4().hex[:6].upper()}"

class ResourceRequest(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_request_id)
    recipient = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE, related_name='resource_requests'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_requests'
    )
    item_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=ResourceCategoryChoices.choices)
    requested_quantity = models.FloatField(validators=[validate_positive_quantity])
    fulfilled_quantity = models.FloatField(default=0.0)
    unit = models.CharField(max_length=30, default='kg')
    priority = models.CharField(
        max_length=20, choices=RequestPriorityChoices.choices, default=RequestPriorityChoices.MEDIUM
    )
    status = models.CharField(
        max_length=30, choices=RequestStatusChoices.choices, default=RequestStatusChoices.OPEN
    )
    people_impacted = models.IntegerField(default=20)
    urgency_deadline = models.DateTimeField()
    delivery_address = models.CharField(max_length=300, blank=True)
    special_instructions = models.TextField(blank=True)
    is_disaster_relief = models.BooleanField(default=False)
    disaster_event = models.ForeignKey(
        'disasters.DisasterEvent', on_delete=models.SET_NULL, null=True, blank=True, related_name='resource_requests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def remaining_quantity(self) -> float:
        return max(0.0, round(self.requested_quantity - self.fulfilled_quantity, 2))

    def clean(self):
        super().clean()
        if self.fulfilled_quantity > self.requested_quantity:
            raise ValidationError('Fulfilled quantity cannot exceed requested quantity.')
        if self.is_disaster_relief and not self.disaster_event:
            raise ValidationError('Disaster relief resource requests must reference an active disaster event.')

    def save(self, *args, **kwargs):
        if not self.delivery_address and self.recipient:
            self.delivery_address = self.recipient.address
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} ({self.requested_quantity} {self.unit}) - {self.recipient.name} [{self.priority}]"
