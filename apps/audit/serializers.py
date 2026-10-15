from rest_framework import serializers
from .models import ActivityLog

class ActivityLogSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='user_id', read_only=True)
    userName = serializers.CharField(source='user_name', read_only=True)
    userRole = serializers.CharField(source='user_role', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'userId', 'userName', 'userRole', 'action', 'details', 'category', 'timestamp']
        read_only_fields = ['id', 'timestamp']
