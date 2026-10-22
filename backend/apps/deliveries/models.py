import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from common.validators import validate_positive_quantity
from apps.requests.models import RequestPriorityChoices

class AllocationStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending Coordinator Approval'
    APPROVED = 'APPROVED', 'Approved'
    FULFILLED = 'FULFILLED', 'Fulfilled & Delivered'
    REJECTED = 'REJECTED', 'Rejected'
    CANCELLED = 'CANCELLED', 'Cancelled'

def generate_allocation_id():
    return f"ALC-{uuid.uuid4().hex[:6].upper()}"

class Allocation(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_allocation_id)
    resource = models.ForeignKey(
        'resources.Resource', on_delete=models.CASCADE, related_name='allocations'
    )
    request = models.ForeignKey(
        'requests.ResourceRequest', on_delete=models.CASCADE, related_name='allocations'
    )
    allocated_quantity = models.FloatField(validators=[validate_positive_quantity])
    status = models.CharField(
        max_length=30, choices=AllocationStatusChoices.choices, default=AllocationStatusChoices.APPROVED
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_allocations'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_allocations'
    )
    ngo_accepted_at = models.DateTimeField(null=True, blank=True)
    ngo_accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_donations')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if self.resource and self.allocated_quantity > self.resource.available_quantity:
            # If existing allocation, allow updating up to available + current
            if not self.pk:
                raise ValidationError(
                    f"Requested allocation ({self.allocated_quantity}) exceeds available resource quantity ({self.resource.available_quantity})."
                )

    def __str__(self):
        return f"{self.id}: {self.allocated_quantity} {self.resource.unit} -> {self.request.recipient.name} ({self.status})"

class DeliveryTaskStatusChoices(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available for Pickup'
    ACCEPTED = 'ACCEPTED', 'Mission Accepted'
    ARRIVED_PICKUP = 'ARRIVED_PICKUP', 'Arrived at Donor Facility'
    PICKED_UP = 'PICKED_UP', 'Goods Picked Up / En Route'
    ARRIVED_DELIVERY = 'ARRIVED_DELIVERY', 'Arrived at Destination Shelter'
    DELIVERED = 'DELIVERED', 'Successfully Delivered'
    DECLINED = 'DECLINED', 'Declined by Volunteer'
    CANCELLED = 'CANCELLED', 'Cancelled'
    DISRUPTED = 'DISRUPTED', 'Route Disrupted / Blocked'

def generate_task_id():
    return f"TSK-{uuid.uuid4().hex[:6].upper()}"

class DeliveryTask(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_task_id)
    allocation = models.OneToOneField(
        Allocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_task'
    )
    resource = models.ForeignKey(
        'resources.Resource', on_delete=models.CASCADE, related_name='delivery_tasks'
    )
    request = models.ForeignKey(
        'requests.ResourceRequest', on_delete=models.CASCADE, related_name='delivery_tasks'
    )
    volunteer = models.ForeignKey(
        'volunteers.Volunteer', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_tasks'
    )
    title = models.CharField(max_length=255)
    cargo_description = models.CharField(max_length=255)
    quantity = models.FloatField(validators=[validate_positive_quantity])
    unit = models.CharField(max_length=30, default='kg')
    status = models.CharField(
        max_length=30, choices=DeliveryTaskStatusChoices.choices, default=DeliveryTaskStatusChoices.AVAILABLE
    )
    priority = models.CharField(
        max_length=20, choices=RequestPriorityChoices.choices, default=RequestPriorityChoices.MEDIUM
    )
    pickup_address = models.CharField(max_length=300)
    delivery_address = models.CharField(max_length=300)
    pickup_contact_phone = models.CharField(max_length=50, blank=True)
    delivery_contact_phone = models.CharField(max_length=50, blank=True)
    pickup_time_window = models.CharField(max_length=100, blank=True)
    delivery_deadline = models.DateTimeField()
    estimated_duration_min = models.IntegerField(default=25)
    is_disaster_mode = models.BooleanField(default=False)
    disaster_event = models.ForeignKey(
        'disasters.DisasterEvent', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_tasks'
    )
    disruption_reason = models.TextField(blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_pickup_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    arrived_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    receipt_confirmed_at = models.DateTimeField(null=True, blank=True)
    receipt_confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_delivery_receipts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def volunteer_name(self):
        return self.volunteer.full_name if self.volunteer else None

    @property
    def quantity_description(self):
        return f"{self.quantity} {self.unit}"

    def can_transition_to(self, target_status: str) -> bool:
        """Enforces valid lifecycle state machine transitions."""
        if self.status == DeliveryTaskStatusChoices.DISRUPTED:
            event = self.status_events.filter(to_status='DISRUPTED').last()
            previous = event.from_status if event else ('ARRIVED_DELIVERY' if self.arrived_delivery_at else 'PICKED_UP' if self.picked_up_at else 'ARRIVED_PICKUP' if self.arrived_pickup_at else 'ACCEPTED')
            return target_status in [previous, 'CANCELLED']
        valid_transitions = {
            DeliveryTaskStatusChoices.AVAILABLE: [DeliveryTaskStatusChoices.ACCEPTED, DeliveryTaskStatusChoices.CANCELLED],
            DeliveryTaskStatusChoices.ACCEPTED: [DeliveryTaskStatusChoices.ARRIVED_PICKUP, DeliveryTaskStatusChoices.DECLINED, DeliveryTaskStatusChoices.CANCELLED, DeliveryTaskStatusChoices.DISRUPTED],
            DeliveryTaskStatusChoices.ARRIVED_PICKUP: [DeliveryTaskStatusChoices.PICKED_UP, DeliveryTaskStatusChoices.DISRUPTED, DeliveryTaskStatusChoices.CANCELLED],
            DeliveryTaskStatusChoices.PICKED_UP: [DeliveryTaskStatusChoices.ARRIVED_DELIVERY, DeliveryTaskStatusChoices.DISRUPTED],
            DeliveryTaskStatusChoices.ARRIVED_DELIVERY: [DeliveryTaskStatusChoices.DELIVERED, DeliveryTaskStatusChoices.DISRUPTED],
            DeliveryTaskStatusChoices.DELIVERED: [],
            DeliveryTaskStatusChoices.DISRUPTED: [DeliveryTaskStatusChoices.ACCEPTED, DeliveryTaskStatusChoices.CANCELLED],
            DeliveryTaskStatusChoices.DECLINED: [DeliveryTaskStatusChoices.AVAILABLE],
            DeliveryTaskStatusChoices.CANCELLED: [],
        }
        return target_status in valid_transitions.get(self.status, [])

    def __str__(self):
        vol = self.volunteer.user.name if self.volunteer else "Unassigned"
        return f"{self.title} ({self.status}) - Courier: {vol}"


def generate_status_event_id():
    return f"EVT-{uuid.uuid4().hex[:8].upper()}"


class DeliveryStatusEvent(models.Model):
    """
    Append-only status audit event record for delivery lifecycle transitions.
    Records authenticated changer, previous state, new state, notes, and exact timestamp.
    """
    id = models.CharField(max_length=64, primary_key=True, default=generate_status_event_id)
    delivery_task = models.ForeignKey(
        DeliveryTask, on_delete=models.CASCADE, related_name='status_events'
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30, choices=DeliveryTaskStatusChoices.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_status_events'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.delivery_task.id}] {self.from_status} -> {self.to_status} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

