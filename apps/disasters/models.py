import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class DisasterTypeChoices(models.TextChoices):
    FLOOD = 'flood', 'Monsoon Flash Floods'
    LANDSLIDE = 'landslide', 'Landslide Risk'
    CYCLONE = 'cyclone', 'Cyclone & Coastal Inundation'
    DROUGHT = 'drought', 'Drought & Water Shortage'
    INDUSTRIAL = 'industrial', 'Industrial / Urban Hazard'

class DisasterSeverityChoices(models.TextChoices):
    LOW = 'low', 'Low Advisory'
    MEDIUM = 'medium', 'Medium Threat'
    HIGH = 'high', 'High Emergency'
    CRITICAL = 'critical', 'Critical Disaster (Category 4/5)'

class DisasterStatusChoices(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft Notice'
    ACTIVE = 'ACTIVE', 'Active Disaster Response'
    RESOLVED = 'RESOLVED', 'Resolved & Recovery'
    CLOSED = 'CLOSED', 'Archived / Closed'

def generate_disaster_id():
    return f"DIS-{uuid.uuid4().hex[:6].upper()}"

class DisasterEvent(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_disaster_id)
    title = models.CharField(max_length=255)
    description = models.TextField()
    disaster_type = models.CharField(
        max_length=30, choices=DisasterTypeChoices.choices, default=DisasterTypeChoices.FLOOD
    )
    severity = models.CharField(
        max_length=20, choices=DisasterSeverityChoices.choices, default=DisasterSeverityChoices.HIGH
    )
    status = models.CharField(
        max_length=20, choices=DisasterStatusChoices.choices, default=DisasterStatusChoices.ACTIVE
    )
    affected_location = models.CharField(max_length=255, default='Moratuwa & Colombo South Lowlands')
    affected_population = models.IntegerField(default=4500)
    declared_at = models.DateTimeField(default=timezone.now)
    declared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='declared_disasters'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_disasters'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-declared_at']

    @property
    def is_active(self) -> bool:
        return self.status == DisasterStatusChoices.ACTIVE

    def __str__(self):
        return f"{self.title} ({self.status}) - {self.affected_location}"
