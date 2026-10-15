from rest_framework import serializers
from .models import Allocation, DeliveryTask

class AllocationSerializer(serializers.ModelSerializer):
    resourceName = serializers.CharField(source='resource.name', read_only=True)
    requestItemName = serializers.CharField(source='request.item_name', read_only=True)
    recipientName = serializers.CharField(source='request.recipient.name', read_only=True)
    providerName = serializers.CharField(source='resource.provider.name', read_only=True)
    allocatedQuantity = serializers.FloatField(source='allocated_quantity')
    deliveryTaskId = serializers.CharField(source='delivery_task.id', read_only=True)
    createdByName = serializers.CharField(source='created_by.name', read_only=True)
    approvedByName = serializers.CharField(source='approved_by.name', read_only=True)

    class Meta:
        model = Allocation
        fields = [
            'id', 'resource', 'resourceName', 'providerName', 'request',
            'requestItemName', 'recipientName', 'allocatedQuantity', 'deliveryTaskId', 'status',
            'created_by', 'createdByName', 'approved_by', 'approvedByName',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_by', 'approved_by', 'created_at', 'updated_at']

class DeliveryTaskSerializer(serializers.ModelSerializer):
    cargoDescription = serializers.CharField(source='cargo_description')
    quantityDescription = serializers.CharField(source='quantity_description', read_only=True)
    volunteerName = serializers.CharField(source='volunteer_name', read_only=True)
    pickupAddress = serializers.CharField(source='pickup_address')
    deliveryAddress = serializers.CharField(source='delivery_address')
    pickupContactPhone = serializers.CharField(source='pickup_contact_phone', required=False, allow_blank=True)
    deliveryContactPhone = serializers.CharField(source='delivery_contact_phone', required=False, allow_blank=True)
    pickupTimeWindow = serializers.CharField(source='pickup_time_window', required=False, allow_blank=True)
    deliveryDeadline = serializers.DateTimeField(source='delivery_deadline')
    estimatedDurationMin = serializers.IntegerField(source='estimated_duration_min', required=False)
    isDisasterMode = serializers.BooleanField(source='is_disaster_mode', required=False)
    disruptionReason = serializers.CharField(source='disruption_reason', required=False, allow_blank=True)

    class Meta:
        model = DeliveryTask
        fields = [
            'id', 'allocation', 'resource', 'request', 'volunteer', 'volunteerName',
            'title', 'cargoDescription', 'quantity', 'unit', 'quantityDescription',
            'status', 'priority', 'pickupAddress', 'deliveryAddress',
            'pickupContactPhone', 'deliveryContactPhone', 'pickupTimeWindow',
            'deliveryDeadline', 'estimatedDurationMin', 'isDisasterMode',
            'disaster_event', 'disruptionReason', 'accepted_at', 'picked_up_at',
            'delivered_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'allocation', 'resource', 'request', 'volunteer',
            'accepted_at', 'picked_up_at', 'delivered_at', 'created_at', 'updated_at'
        ]
