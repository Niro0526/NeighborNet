import uuid
from django.db import models
from django.conf import settings

class OrganizationTypeChoices(models.TextChoices):
    RESTAURANT = 'RESTAURANT', 'Restaurant'
    BAKERY = 'BAKERY', 'Bakery'
    SUPERMARKET = 'SUPERMARKET', 'Supermarket'
    HOTEL = 'HOTEL', 'Hotel & Catering'
    FOOD_BANK = 'FOOD_BANK', 'Food Bank'
    NGO = 'NGO', 'Non-Governmental Organization'
    SHELTER = 'SHELTER', 'Community Shelter'
    COMMUNITY_KITCHEN = 'COMMUNITY_KITCHEN', 'Community Kitchen'
    RELIEF_CENTER = 'RELIEF_CENTER', 'Disaster Relief Center'
    GOVERNMENT_DISASTER_DESK = 'GOVERNMENT_DISASTER_DESK', 'Government Disaster Desk'

def generate_org_id():
    return f"ORG-{uuid.uuid4().hex[:6].upper()}"

class Organization(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_org_id)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=OrganizationTypeChoices.choices)
    registration_number = models.CharField(max_length=100, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_organizations'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=50)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100, default='Moratuwa')
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.FloatField(default=6.7730)
    longitude = models.FloatField(default=79.8816)
    capacity = models.IntegerField(null=True, blank=True, help_text='Daily beneficiary or meal capacity')
    operating_hours = models.CharField(max_length=100, blank=True)
    service_area = models.CharField(max_length=200, blank=True, default='Western Province - Moratuwa & Colombo South')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['name']

    @property
    def coordinates(self):
        return {'latitude': self.latitude, 'longitude': self.longitude}

    def __str__(self):
        status = "Verified" if self.verified else "Unverified"
        return f"{self.name} ({self.get_type_display()}) - {status}"

class MembershipRoleChoices(models.TextChoices):
    OWNER = 'OWNER', 'Owner'
    ADMIN = 'ADMIN', 'Administrator'
    STAFF = 'STAFF', 'Staff Member'

class OrganizationMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organization_memberships')
    role = models.CharField(max_length=20, choices=MembershipRoleChoices.choices, default=MembershipRoleChoices.ADMIN)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"
