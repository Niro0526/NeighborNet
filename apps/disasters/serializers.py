from rest_framework import serializers
from .models import DisasterEvent

class DisasterEventSerializer(serializers.ModelSerializer):
    disasterType = serializers.CharField(source='disaster_type')
    affectedLocation = serializers.CharField(source='affected_location')
    affectedPopulation = serializers.IntegerField(source='affected_population')
    declaredAt = serializers.DateTimeField(source='declared_at', read_only=True)
    declaredByName = serializers.CharField(source='declared_by.name', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)

    class Meta:
        model = DisasterEvent
        fields = [
            'id', 'title', 'description', 'disasterType', 'severity', 'status',
            'affectedLocation', 'affectedPopulation', 'declaredAt', 'declaredByName',
            'resolved_at', 'isActive', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'declaredAt', 'resolved_at', 'created_at', 'updated_at']
