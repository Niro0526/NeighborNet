from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    actionUrl = serializers.CharField(source='action_url', required=False, allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'read', 'actionUrl', 'createdAt']
        read_only_fields = ['id', 'createdAt']
