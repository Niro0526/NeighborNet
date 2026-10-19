from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    actionUrl = serializers.CharField(source='action_url', required=False, allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    targetRole = serializers.CharField(source='role_target', read_only=True)
    organizationName = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'organization', 'organizationName', 'role_target',
            'targetRole', 'title', 'message', 'type', 'read', 'actionUrl',
            'action_url', 'createdAt', 'created_at'
        ]
        read_only_fields = ['id', 'createdAt', 'created_at']

