from rest_framework import serializers
from .models import DisasterEvent

class DisasterEventSerializer(serializers.ModelSerializer):
    disasterType = serializers.CharField(source='disaster_type')
    affectedLocation = serializers.CharField(source='affected_location')
    affectedPopulation = serializers.IntegerField(source='affected_population')
    declaredAt = serializers.DateTimeField(source='declared_at', read_only=True)
    declaredByName = serializers.CharField(source='declared_by.name', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    activeReliefRequestsCount = serializers.SerializerMethodField()
    activeResponseTeamsCount = serializers.SerializerMethodField()

    def get_activeReliefRequestsCount(self, obj):
        from apps.requests.models import ResourceRequest
        return ResourceRequest.objects.filter(disaster_event=obj).exclude(status__in=['FULFILLED', 'CANCELLED']).count()

    def get_activeResponseTeamsCount(self, obj):
        from apps.deliveries.models import DeliveryTask
        return DeliveryTask.objects.filter(disaster_event=obj, volunteer__isnull=False).exclude(status__in=['DELIVERED', 'CANCELLED', 'FAILED']).values('volunteer_id').distinct().count()

    class Meta:
        model = DisasterEvent
        fields = [
            'id', 'title', 'description', 'disasterType', 'severity', 'status',
            'affectedLocation', 'affectedPopulation', 'declaredAt', 'declaredByName',
            'resolved_at', 'isActive', 'created_at', 'updated_at', 'activeReliefRequestsCount', 'activeResponseTeamsCount'
        ]
        read_only_fields = ['id', 'declaredAt', 'resolved_at', 'created_at', 'updated_at']
