from rest_framework import viewsets
from .models import ActivityLog
from .serializers import ActivityLogSerializer
from common.permissions import IsCoordinator

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Immutable System Audit Trail.
    Restricted strictly to approved Coordinators.
    """
    queryset = ActivityLog.objects.all().select_related('user')
    serializer_class = ActivityLogSerializer
    permission_classes = [IsCoordinator]
    filterset_fields = ['category', 'action', 'user_role']
    search_fields = ['user_name', 'action', 'details']
    ordering_fields = ['timestamp']
