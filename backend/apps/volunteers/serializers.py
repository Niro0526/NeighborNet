from rest_framework import serializers
from .models import Volunteer

class VolunteerSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='user.id', read_only=True)
    fullName = serializers.CharField(source='full_name', read_only=True)
    phone = serializers.CharField(read_only=True)
    vehicleType = serializers.CharField(source='vehicle_type')
    vehicleCapacityKg = serializers.FloatField(source='vehicle_capacity_kg')
    completedDeliveriesCount = serializers.SerializerMethodField()
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
            , 'transport_storage', 'travel_speed_kmh'
        ]
        read_only_fields = ['id', 'verified', 'completedDeliveriesCount', 'rating', 'created_at', 'updated_at']

    def validate(self, attrs):
        import math
        if 'vehicle_capacity_kg' in attrs and (not math.isfinite(attrs['vehicle_capacity_kg']) or attrs['vehicle_capacity_kg'] <= 0):
            raise serializers.ValidationError('Recorded capacity must be finite and positive.')
        if attrs.get('travel_speed_kmh') is not None and (not math.isfinite(attrs['travel_speed_kmh']) or attrs['travel_speed_kmh'] <= 0):
            raise serializers.ValidationError('Recorded speed must be finite and positive.')
        if attrs.get('transport_storage') is not None and (not isinstance(attrs['transport_storage'], list) or any(not isinstance(v, str) for v in attrs['transport_storage'])):
            raise serializers.ValidationError('Transport storage must be a list of documented capabilities.')
        return attrs

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if not user.is_coordinator and any(k in validated_data and validated_data[k] != getattr(instance, k) for k in ['transport_storage', 'travel_speed_kmh', 'vehicle_capacity_kg']):
            validated_data['verified'] = False
        return super().update(instance, validated_data)

    def get_coordinates(self, obj):
        # Privacy protection: only expose location if request user is volunteer or coordinator
        request = self.context.get('request')
        if request and (request.user.is_coordinator or request.user == obj.user):
            return obj.coordinates
        return None

    def get_completedDeliveriesCount(self, obj):
        from apps.deliveries.models import DeliveryTask
        return DeliveryTask.objects.filter(volunteer=obj, status='DELIVERED').count()

    def get_profileCompletion(self, obj):
        fields_checked = [obj.user.phone, obj.user.name, obj.vehicle_type, obj.vehicle_capacity_kg, obj.service_area]
        filled = sum(1 for f in fields_checked if f)
        return int((filled / len(fields_checked)) * 100)

