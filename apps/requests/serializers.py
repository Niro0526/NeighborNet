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
        ]
        read_only_fields = ['id', 'recipient', 'fulfilledQuantity', 'created_at', 'updated_at']

    def validate(self, attrs):
        is_disaster = attrs.get('is_disaster_relief', False)
        disaster_event_id = attrs.get('disaster_event_id')
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

    def create(self, validated_data):
        recipient_id = validated_data.pop('recipient_id', None)
        request = self.context.get('request')
        if recipient_id:
            from apps.organizations.models import Organization
            validated_data['recipient'] = Organization.objects.get(id=recipient_id)
        elif request and request.user.organization_memberships.exists():
            validated_data['recipient'] = request.user.organization_memberships.first().organization
        else:
            raise serializers.ValidationError('A recipient organization is required to create resource requests.')

        validated_data['created_by'] = request.user if request else None
        return super().create(validated_data)
