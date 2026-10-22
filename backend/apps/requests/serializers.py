from rest_framework import serializers
from .models import ResourceRequest

class ResourceRequestSerializer(serializers.ModelSerializer):
    recipientId = serializers.CharField(source='recipient.id', read_only=True)
    recipientName = serializers.CharField(source='recipient.name', read_only=True)
    recipient_id = serializers.CharField(write_only=True, required=False)
    requestedQuantity = serializers.FloatField(source='requested_quantity')
    fulfilledQuantity = serializers.FloatField(source='fulfilled_quantity', read_only=True)
    remainingQuantity = serializers.FloatField(source='remaining_quantity', read_only=True)
    peopleImpacted = serializers.IntegerField(source='people_impacted', required=False)
    urgencyDeadline = serializers.DateTimeField(source='urgency_deadline')
    deliveryAddress = serializers.CharField(source='delivery_address', required=False, allow_blank=True)
    specialInstructions = serializers.CharField(source='special_instructions', required=False, allow_blank=True)
    isDisasterRelief = serializers.BooleanField(source='is_disaster_relief', required=False)
    disasterEventId = serializers.CharField(source='disaster_event_id', required=False, allow_null=True)

    class Meta:
        model = ResourceRequest
        fields = [
            'id', 'recipient', 'recipientId', 'recipient_id', 'recipientName',
            'item_name', 'category', 'requestedQuantity', 'fulfilledQuantity',
            'remainingQuantity', 'unit', 'priority', 'status', 'peopleImpacted',
            'urgencyDeadline', 'deliveryAddress', 'specialInstructions',
            'isDisasterRelief', 'disasterEventId', 'created_at', 'updated_at'
            , 'delivery_latitude', 'delivery_longitude', 'allow_partial'
        ]
        read_only_fields = ['id', 'status', 'recipient', 'fulfilledQuantity', 'created_at', 'updated_at']

    def validate(self, attrs):
        import math
        if 'requested_quantity' in attrs and (not math.isfinite(attrs['requested_quantity']) or attrs['requested_quantity'] <= 0 or abs(attrs['requested_quantity']-round(attrs['requested_quantity'], 2)) > 1e-9):
            raise serializers.ValidationError({'requestedQuantity': 'Use a finite positive quantity with at most two decimal places.'})
        lat = attrs.get('delivery_latitude', getattr(self.instance, 'delivery_latitude', None))
        lon = attrs.get('delivery_longitude', getattr(self.instance, 'delivery_longitude', None))
        if (lat is None) != (lon is None) or (lat is not None and (not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180)):
            raise serializers.ValidationError('Provide a valid delivery latitude and longitude together.')
        from django.utils import timezone
        if 'urgency_deadline' in attrs and attrs['urgency_deadline'] <= timezone.now():
            raise serializers.ValidationError({'urgencyDeadline': 'The deadline must be in the future.'})
        is_disaster = attrs.get('is_disaster_relief', getattr(self.instance, 'is_disaster_relief', False))
        disaster_event_id = attrs.get('disaster_event_id', getattr(self.instance, 'disaster_event_id', None))
        if self.instance and attrs.get('requested_quantity', self.instance.requested_quantity) < self.instance.fulfilled_quantity:
            raise serializers.ValidationError('Requested quantity cannot be below reserved allocations.')
        if is_disaster:
            if not disaster_event_id:
                raise serializers.ValidationError('Disaster relief resource requests must reference an active disaster event.')
            from apps.disasters.models import DisasterEvent, DisasterStatusChoices
            try:
                event = DisasterEvent.objects.get(id=disaster_event_id)
                if event.status != DisasterStatusChoices.ACTIVE:
                    raise serializers.ValidationError('Disaster relief resource requests must reference an active disaster event.')
            except DisasterEvent.DoesNotExist:
                raise serializers.ValidationError('Referenced disaster event does not exist.')
        return attrs

    def to_representation(self, instance):
        data=super().to_representation(instance)
        request=self.context.get('request')
        if request and not request.user.is_coordinator and not (request.user.is_recipient and instance.recipient.memberships.filter(user=request.user,is_active=True).exists()):
            data['deliveryAddress']=''
            data['delivery_latitude']=None
            data['delivery_longitude']=None
            data['specialInstructions']=''
            data['item_name']='Organization resource request'
        return data

    def create(self, validated_data):
        recipient_id = validated_data.pop('recipient_id', None)
        request = self.context.get('request')
        from common.organization_scope import resolve_organization
        validated_data['recipient'] = resolve_organization(request.user, recipient_id)

        validated_data['created_by'] = request.user if request else None
        return super().create(validated_data)
