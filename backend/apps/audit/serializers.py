from rest_framework import serializers
from .models import ActivityLog, PilotFeedback

class ActivityLogSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='user_id', read_only=True)
    userName = serializers.CharField(source='user_name', read_only=True)
    userRole = serializers.CharField(source='user_role', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'userId', 'userName', 'userRole', 'action', 'details', 'category', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class PilotFeedbackSerializer(serializers.ModelSerializer):
    userName = serializers.CharField(source='user_name', read_only=True)
    userRole = serializers.CharField(source='user_role', read_only=True)
    categoryDisplay = serializers.CharField(source='get_category_display', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = PilotFeedback
        fields = [
            'id', 'category', 'categoryDisplay', 'rating', 'comments',
            'consent_to_share_internally', 'user_name', 'userName',
            'user_role', 'userRole', 'createdAt'
        ]
        read_only_fields = ['id', 'user_name', 'user_role', 'createdAt']

