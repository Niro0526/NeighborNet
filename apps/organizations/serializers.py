from rest_framework import serializers
from .models import Organization, OrganizationMembership

class OrganizationSerializer(serializers.ModelSerializer):
    registrationNumber = serializers.CharField(source='registration_number', required=False, allow_blank=True)
    contactEmail = serializers.EmailField(source='contact_email')
    contactPhone = serializers.CharField(source='contact_phone')
    postalCode = serializers.CharField(source='postal_code', required=False, allow_blank=True)
    operatingHours = serializers.CharField(source='operating_hours', required=False, allow_blank=True)
    coordinates = serializers.ReadOnlyField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'type', 'registrationNumber', 'verified',
            'contactEmail', 'contactPhone', 'address', 'city', 'postalCode',
            'latitude', 'longitude', 'coordinates', 'capacity',
            'operatingHours', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verified', 'created_at', 'updated_at']

class OrganizationMembershipSerializer(serializers.ModelSerializer):
    userEmail = serializers.EmailField(source='user.email', read_only=True)
    userName = serializers.CharField(source='user.name', read_only=True)
    organizationName = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            'id', 'organization', 'organizationName', 'user', 'userEmail',
            'userName', 'role', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
