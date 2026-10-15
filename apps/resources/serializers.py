from rest_framework import serializers
from .models import Resource

class ResourceSerializer(serializers.ModelSerializer):
    providerId = serializers.CharField(source='provider.id', read_only=True)
    providerName = serializers.CharField(source='provider.name', read_only=True)
    provider_id = serializers.CharField(write_only=True, required=False)
    availableQuantity = serializers.FloatField(source='available_quantity', read_only=True)
    pickupStart = serializers.DateTimeField(source='pickup_start')
    pickupEnd = serializers.DateTimeField(source='pickup_end')
    safeUntil = serializers.DateTimeField(source='safe_until', required=False, allow_null=True)
    storageRequirements = serializers.CharField(source='storage_requirements', required=False)
    dietaryTags = serializers.ListField(source='dietary_tags', required=False)
    safetyNotes = serializers.CharField(source='safety_notes', required=False, allow_blank=True)
    isDisasterRelief = serializers.BooleanField(source='is_disaster_relief', required=False)
    disasterEventId = serializers.CharField(source='disaster_event_id', required=False, allow_null=True)

    class Meta:
        model = Resource
        fields = [
            'id', 'provider', 'providerId', 'provider_id', 'providerName', 'name', 'category',
            'quantity', 'allocated_quantity', 'availableQuantity', 'unit',
            'pickupStart', 'pickupEnd', 'safeUntil', 'storageRequirements',
            'status', 'dietaryTags', 'safetyNotes', 'isDisasterRelief',
            'disasterEventId', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'allocated_quantity', 'created_at', 'updated_at', 'provider']

    def create(self, validated_data):
        provider_id = validated_data.pop('provider_id', None)
        request = self.context.get('request')
        if provider_id:
            from apps.organizations.models import Organization
            validated_data['provider'] = Organization.objects.get(id=provider_id)
        elif request and request.user.organization_memberships.exists():
            validated_data['provider'] = request.user.organization_memberships.first().organization
        else:
            raise serializers.ValidationError('A provider organization is required to list resources.')

        validated_data['created_by'] = request.user if request else None
        return super().create(validated_data)
