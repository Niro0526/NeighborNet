import uuid
from django.db import models
from django.conf import settings

class VolunteerAvailabilityChoices(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    BUSY = 'busy', 'Busy / On Delivery'
    OFFLINE = 'offline', 'Offline'

class VehicleTypeChoices(models.TextChoices):
    MOTORCYCLE = 'motorcycle', 'Motorcycle / Scooter'
    CAR = 'car', 'Car / Sedan'
    VAN = 'van', 'Van / Light Truck'
    BICYCLE = 'bicycle', 'Bicycle'
    FOOT = 'foot', 'On Foot'

def generate_volunteer_id():
    return f"VOL-{uuid.uuid4().hex[:6].upper()}"

class Volunteer(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_volunteer_id)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='volunteer_profile'
    )
    status = models.CharField(
        max_length=20, choices=VolunteerAvailabilityChoices.choices, default=VolunteerAvailabilityChoices.AVAILABLE
    )
    vehicle_type = models.CharField(
        max_length=20, choices=VehicleTypeChoices.choices, default=VehicleTypeChoices.MOTORCYCLE
    )
    vehicle_capacity_kg = models.FloatField(default=25.0)
    completed_deliveries_count = models.IntegerField(default=0)
    rating = models.FloatField(default=5.0)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_volunteers'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    service_area = models.CharField(max_length=150, default='Moratuwa & Colombo South')
    latitude = models.FloatField(default=6.7730, null=True, blank=True)
    longitude = models.FloatField(default=79.8816, null=True, blank=True)
    badge = models.CharField(max_length=100, blank=True, default='Top Responder')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-completed_deliveries_count']

    @property
    def full_name(self):
        return self.user.name

    @property
    def phone(self):
        return self.user.phone

    @property
    def coordinates(self):
        if self.latitude and self.longitude:
            return {'latitude': self.latitude, 'longitude': self.longitude}
        return None

    def __str__(self):
        return f"{self.user.name} ({self.get_vehicle_type_display()}) - {self.status}"
