from rest_framework import serializers
from .models import Resource
from rest_framework import serializers

class ResourceSerializer(serializers.ModelSerializer):
    providerId = serializers.CharField(source='provider.id', read_only=True)
    providerName = serializers.CharField(source='provider.name', read_only=True)
    provider_id = serializers.CharField(write_only=True, required=False)
    availableQuantity = serializers.FloatField(source='available_quantity', read_only=True)
    pickupStart = serializers.DateTimeField(source='pickup_start')
    pickupEnd = serializers.DateTimeField(source='pickup_end')
    pickupAddress = serializers.CharField(source='pickup_address', required=False, allow_blank=True)
    pickupLatitude = serializers.FloatField(source='pickup_latitude', required=False, allow_null=True)
    pickupLongitude = serializers.FloatField(source='pickup_longitude', required=False, allow_null=True)
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
            'unit_weight_kg',
            'pickupStart', 'pickupEnd', 'safeUntil', 'storageRequirements',
            'pickupAddress', 'pickupLatitude', 'pickupLongitude',
            'status', 'dietaryTags', 'safetyNotes', 'isDisasterRelief',
            'disasterEventId', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'allocated_quantity', 'created_at', 'updated_at', 'provider']

    def validate(self, attrs):
        import math
        if 'quantity' in attrs and (not math.isfinite(attrs['quantity']) or attrs['quantity'] <= 0 or abs(attrs['quantity']-round(attrs['quantity'], 2)) > 1e-9):
            raise serializers.ValidationError({'quantity': 'Use a finite positive quantity with at most two decimal places.'})
        if attrs.get('unit_weight_kg') is not None and (not math.isfinite(attrs['unit_weight_kg']) or attrs['unit_weight_kg'] <= 0):
            raise serializers.ValidationError({'unit_weight_kg': 'Record a finite, positive weight per unit.'})
        attrs = super().validate(attrs)
        if self.instance and attrs.get('quantity', self.instance.quantity) < self.instance.allocated_quantity:
            raise serializers.ValidationError({'quantity': 'Quantity cannot be below reserved inventory.'})
        if attrs.get('is_disaster_relief', getattr(self.instance, 'is_disaster_relief', False)):
            from apps.disasters.models import DisasterEvent
            event_id = attrs.get('disaster_event_id', getattr(self.instance, 'disaster_event_id', None))
            if not DisasterEvent.objects.filter(pk=event_id, status='ACTIVE').exists():
                raise serializers.ValidationError('Relief supplies require an active disaster event.')
        latitude = attrs.get('pickup_latitude', getattr(self.instance, 'pickup_latitude', None))
        longitude = attrs.get('pickup_longitude', getattr(self.instance, 'pickup_longitude', None))
        address = attrs.get('pickup_address', getattr(self.instance, 'pickup_address', ''))
        location_supplied = any(
            key in attrs for key in ('pickup_address', 'pickup_latitude', 'pickup_longitude')
        )
        if location_supplied and (not address or not address.strip()):
            raise serializers.ValidationError({'pickupAddress': 'A pickup address is required.'})
        if location_supplied and (latitude is None or not -90 <= latitude <= 90):
            raise serializers.ValidationError({'pickupLatitude': 'Enter a valid latitude.'})
        if location_supplied and (longitude is None or not -180 <= longitude <= 180):
            raise serializers.ValidationError({'pickupLongitude': 'Enter a valid longitude.'})
        pickup_start = attrs.get('pickup_start', getattr(self.instance, 'pickup_start', None))
        pickup_end = attrs.get('pickup_end', getattr(self.instance, 'pickup_end', None))
        safe_until = attrs.get('safe_until', getattr(self.instance, 'safe_until', None))
        if pickup_start and pickup_end and pickup_end <= pickup_start:
            raise serializers.ValidationError({'pickupEnd': 'Pickup end must be after pickup start.'})
        if safe_until and pickup_end and safe_until < pickup_end:
            raise serializers.ValidationError({'safeUntil': 'Safe-consumption deadline must cover the pickup window.'})
        return attrs

    def create(self, validated_data):
        provider_id = validated_data.pop('provider_id', None)
        request = self.context.get('request')
        from common.organization_scope import resolve_organization
        validated_data['provider'] = resolve_organization(request.user, provider_id, provider=True)

        provider = validated_data['provider']
        validated_data.setdefault('pickup_address', provider.address)
        validated_data.setdefault('pickup_latitude', provider.latitude)
        validated_data.setdefault('pickup_longitude', provider.longitude)
        validated_data['created_by'] = request.user if request else None
        return super().create(validated_data)
