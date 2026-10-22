import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from common.validators import validate_positive_quantity

class ResourceCategoryChoices(models.TextChoices):
    COOKED_MEALS = 'cooked_meals', 'Cooked Meals'
    BAKERY = 'bakery', 'Bakery Items'
    FRESH_PRODUCE = 'fresh_produce', 'Fresh Produce'
    DAIRY = 'dairy', 'Dairy Products'
    CANNED_PACKAGED = 'canned_packaged', 'Canned & Packaged Food'
    BEVERAGES = 'beverages', 'Beverages'
    DRINKING_WATER = 'drinking_water', 'Drinking Water Cans / Bottles'
    HYGIENE_KITS = 'hygiene_kits', 'Hygiene & Sanitization Kits'
    BLANKETS_BEDDING = 'blankets_bedding', 'Blankets & Bedding'
    MEDICAL_SUPPLIES = 'medical_supplies', 'Basic Medical Supplies & First Aid'

class ResourceStatusChoices(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    RESERVED = 'RESERVED', 'Reserved'
    COLLECTED = 'COLLECTED', 'Collected'
    DEPLETED = 'DEPLETED', 'Depleted'
    EXPIRED = 'EXPIRED', 'Expired'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

class StorageRequirementChoices(models.TextChoices):
    AMBIENT = 'Ambient', 'Ambient Room Temp'
    REFRIGERATED = 'Refrigerated', 'Refrigerated (<4°C)'
    FROZEN = 'Keep Frozen', 'Keep Frozen (<-18°C)'
    KEEP_WARM = 'Keep Warm (>60°C)', 'Keep Warm (>60°C)'

def generate_resource_id():
    return f"RES-{uuid.uuid4().hex[:6].upper()}"

class Resource(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_resource_id)
    provider = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE, related_name='resources'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_resources'
    )
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=ResourceCategoryChoices.choices)
    quantity = models.FloatField(validators=[validate_positive_quantity])
    allocated_quantity = models.FloatField(default=0.0)
    unit = models.CharField(max_length=30, default='kg')
    unit_weight_kg = models.FloatField(null=True, blank=True, help_text='Recorded kg per unit for courier capacity; never inferred')
    pickup_start = models.DateTimeField()
    pickup_end = models.DateTimeField()
    pickup_address = models.CharField(max_length=300, blank=True, default='')
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    safe_until = models.DateTimeField(null=True, blank=True, help_text='Perishable food expiry deadline')
    storage_requirements = models.CharField(
        max_length=50, choices=StorageRequirementChoices.choices, default=StorageRequirementChoices.AMBIENT
    )
    status = models.CharField(
        max_length=30, choices=ResourceStatusChoices.choices, default=ResourceStatusChoices.AVAILABLE
    )
    dietary_tags = models.JSONField(default=list, blank=True)
    safety_notes = models.TextField(blank=True)
    is_disaster_relief = models.BooleanField(default=False)
    disaster_event = models.ForeignKey(
        'disasters.DisasterEvent', on_delete=models.SET_NULL, null=True, blank=True, related_name='resources'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def available_quantity(self) -> float:
        remaining = self.quantity - self.allocated_quantity
        return max(0.0, round(remaining, 2))

    @property
    def is_food(self) -> bool:
        food_categories = {
            ResourceCategoryChoices.COOKED_MEALS,
            ResourceCategoryChoices.BAKERY,
            ResourceCategoryChoices.FRESH_PRODUCE,
            ResourceCategoryChoices.DAIRY,
            ResourceCategoryChoices.CANNED_PACKAGED,
            ResourceCategoryChoices.BEVERAGES,
        }
        return self.category in food_categories

    def clean(self):
        super().clean()
        if self.allocated_quantity > self.quantity:
            raise ValidationError('Allocated quantity cannot exceed total resource quantity.')

    def save(self, *args, **kwargs):
        self.clean()
        # Automatically update status to DEPLETED if fully allocated
        if self.available_quantity <= 0 and self.status == ResourceStatusChoices.AVAILABLE:
            self.status = ResourceStatusChoices.RESERVED
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit}) - {self.provider.name}"
