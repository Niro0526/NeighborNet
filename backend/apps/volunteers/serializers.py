from rest_framework import serializers
from .models import Volunteer

class VolunteerSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='user.id', read_only=True)
    fullName = serializers.CharField(source='full_name', read_only=True)
    phone = serializers.CharField(read_only=True)
    vehicleType = serializers.CharField(source='vehicle_type')
    vehicleCapacityKg = serializers.FloatField(source='vehicle_capacity_kg')
    completedDeliveriesCount = serializers.IntegerField(source='completed_deliveries_count', read_only=True)
    serviceArea = serializers.CharField(source='service_area')
    coordinates = serializers.SerializerMethodField()
    profileCompletion = serializers.SerializerMethodField()

    class Meta:
        model = Volunteer
        fields = [
            'id', 'userId', 'fullName', 'phone', 'status', 'vehicleType',
            'vehicleCapacityKg', 'completedDeliveriesCount', 'rating',
            'verified', 'serviceArea', 'badge', 'coordinates', 'profileCompletion',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verified', 'completedDeliveriesCount', 'rating', 'created_at', 'updated_at']

    def get_coordinates(self, obj):
        # Privacy protection: only expose location if request user is volunteer or coordinator
        request = self.context.get('request')
        if request and (request.user.is_coordinator or request.user == obj.user):
            return obj.coordinates
        return None

    def get_profileCompletion(self, obj):
        fields_checked = [obj.user.phone, obj.user.name, obj.vehicle_type, obj.vehicle_capacity_kg, obj.service_area]
        filled = sum(1 for f in fields_checked if f)
        return int((filled / len(fields_checked)) * 100)

