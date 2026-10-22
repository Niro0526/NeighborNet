from rest_framework import serializers
from .models import Allocation, DeliveryTask, DeliveryStatusEvent

class AllocationSerializer(serializers.ModelSerializer):
    unit = serializers.CharField(source='resource.unit', read_only=True)
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
            'id', 'unit', 'resource', 'resourceName', 'providerName', 'request',
            'requestItemName', 'recipientName', 'allocatedQuantity', 'deliveryTaskId', 'status',
            'created_by', 'createdByName', 'approved_by', 'approvedByName',
            'created_at', 'updated_at', 'ngo_accepted_at', 'approved_at'
        ]
        read_only_fields = ['id', 'status', 'created_by', 'approved_by', 'created_at', 'updated_at', 'ngo_accepted_at', 'approved_at']

    def to_representation(self, instance):
        data=super().to_representation(instance)
        request=self.context.get('request')
        if request and not request.user.is_coordinator and not instance.request.recipient.memberships.filter(user=request.user,is_active=True).exists():
            for key in ['created_by','createdByName','requestItemName']:
                data.pop(key,None)
        return data

class DeliveryStatusEventSerializer(serializers.ModelSerializer):
    changedByName = serializers.CharField(source='changed_by.name', read_only=True)
    fromStatus = serializers.CharField(source='from_status')
    toStatus = serializers.CharField(source='to_status')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = DeliveryStatusEvent
        fields = ['id', 'fromStatus', 'toStatus', 'changed_by', 'changedByName', 'notes', 'createdAt']
        read_only_fields = ['id', 'createdAt']

class DeliveryTaskSerializer(serializers.ModelSerializer):
    allocationStatus = serializers.CharField(source='allocation.status',read_only=True)
    providerName = serializers.CharField(source='resource.provider.name',read_only=True)
    recipientName = serializers.CharField(source='request.recipient.name',read_only=True)
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
    statusEvents = DeliveryStatusEventSerializer(source='status_events', many=True, read_only=True)
    arrivedPickupAt = serializers.DateTimeField(source='arrived_pickup_at', read_only=True)
    arrivedDeliveryAt = serializers.DateTimeField(source='arrived_delivery_at', read_only=True)
    acceptedAt = serializers.DateTimeField(source='accepted_at', read_only=True)
    pickedUpAt = serializers.DateTimeField(source='picked_up_at', read_only=True)
    deliveredAt = serializers.DateTimeField(source='delivered_at', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = DeliveryTask
        fields = [
            'id', 'allocation', 'allocationStatus', 'providerName', 'recipientName', 'resource', 'request', 'volunteer', 'volunteerName',
            'title', 'cargoDescription', 'quantity', 'unit', 'quantityDescription',
            'status', 'priority', 'pickupAddress', 'deliveryAddress',
            'pickupContactPhone', 'deliveryContactPhone', 'pickupTimeWindow',
            'deliveryDeadline', 'estimatedDurationMin', 'isDisasterMode',
            'disaster_event', 'disruptionReason', 'accepted_at', 'picked_up_at',
            'arrived_pickup_at', 'arrived_delivery_at', 'delivered_at',
            'acceptedAt', 'pickedUpAt', 'arrivedPickupAt', 'arrivedDeliveryAt', 'deliveredAt',
            'statusEvents', 'created_at', 'updated_at', 'createdAt', 'updatedAt', 'assigned_at', 'receipt_confirmed_at'
        ]
        read_only_fields = [
            'id', 'allocation', 'resource', 'request', 'volunteer',
            'accepted_at', 'picked_up_at', 'arrived_pickup_at', 'arrived_delivery_at', 'delivered_at',
            'created_at', 'updated_at', 'assigned_at', 'receipt_confirmed_at'
        ]

    def to_representation(self, instance):
        data=super().to_representation(instance)
        request=self.context.get('request')
        if not request:
            return data
        user=request.user
        recipient=user.is_recipient and instance.request.recipient.memberships.filter(user=user,is_active=True).exists()
        courier=user.is_volunteer and instance.volunteer_id and instance.volunteer.user_id==user.pk
        if not (user.is_coordinator or recipient or courier):
            data['deliveryAddress']=''
            data['deliveryContactPhone']=''
            data['disruptionReason']=''
            for event in data['statusEvents']:
                for key in ['changed_by','changedByName','notes']:
                    event.pop(key,None)
            provider=user.is_food_provider and instance.resource.provider.memberships.filter(user=user,is_active=True).exists()
            if not provider:
                data['pickupContactPhone']=''
        return data

