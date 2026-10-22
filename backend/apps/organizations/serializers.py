from rest_framework import serializers
from .models import Organization, OrganizationMembership

class OrganizationSerializer(serializers.ModelSerializer):
    registrationNumber = serializers.CharField(source='registration_number', required=False, allow_blank=True)
    contactEmail = serializers.EmailField(source='contact_email')
    contactPhone = serializers.CharField(source='contact_phone')
    postalCode = serializers.CharField(source='postal_code', required=False, allow_blank=True)
    operatingHours = serializers.CharField(source='operating_hours', required=False, allow_blank=True)
    serviceArea = serializers.CharField(source='service_area', required=False, allow_blank=True)
    coordinates = serializers.ReadOnlyField()
    profileCompletion = serializers.SerializerMethodField()
    missingProfileFields = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'type', 'registrationNumber', 'verified',
            'contactEmail', 'contactPhone', 'address', 'city', 'postalCode',
            'latitude', 'longitude', 'coordinates', 'capacity',
            'operatingHours', 'serviceArea', 'description', 'profileCompletion',
            'dietary_requirements', 'storage_capabilities', 'matching_preferences_verified',
            'missingProfileFields', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verified', 'matching_preferences_verified', 'created_at', 'updated_at']

    def validate(self, attrs):
        for key in ['dietary_requirements', 'storage_capabilities']:
            if key in attrs and attrs[key] is not None and (not isinstance(attrs[key], list) or any(not isinstance(v, str) or not v.strip() for v in attrs[key])):
                raise serializers.ValidationError({key: 'Use a list of recorded requirements, or null for unknown.'})
        return attrs

    def update(self, instance, validated_data):
        if any(key in validated_data and validated_data[key] != getattr(instance, key) for key in ['dietary_requirements', 'storage_capabilities', 'operating_hours']):
            validated_data['matching_preferences_verified'] = False
        return super().update(instance, validated_data)

    def get_missingProfileFields(self, obj):
        missing = []
        if not obj.registration_number:
            missing.append('Business/NGO Registration Number')
        if not obj.contact_phone:
            missing.append('Primary Contact Phone')
        if not obj.address:
            missing.append('Physical Address')
        if not obj.capacity:
            missing.append('Daily Capacity')
        if not obj.operating_hours:
            missing.append('Operating Hours')
        if not obj.service_area:
            missing.append('Service Area Specification')
        return missing

    def get_profileCompletion(self, obj):
        total_fields = 6
        missing = len(self.get_missingProfileFields(obj))
        completed = total_fields - missing
        return int((completed / total_fields) * 100)


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
