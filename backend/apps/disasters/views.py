from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import DisasterEvent, DisasterStatusChoices
from .serializers import DisasterEventSerializer
from common.permissions import IsCoordinator
from apps.audit.models import ActivityLog, AuditCategoryChoices

from apps.notifications.services import send_notification

class DisasterEventViewSet(viewsets.ModelViewSet):
    queryset = DisasterEvent.objects.all()
    serializer_class = DisasterEventSerializer
    filterset_fields = ['status', 'severity', 'disaster_type']
    search_fields = ['title', 'description', 'affected_location']
    ordering_fields = ['declared_at', 'severity']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'activate', 'resolve']:
            return [IsCoordinator()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        disaster = serializer.save(declared_by=self.request.user)
        ActivityLog.objects.create(
            user=self.request.user,
            user_name=self.request.user.name,
            user_role='COORDINATOR',
            action='DISASTER_EVENT_CREATED',
            details=f"Declared disaster event: {disaster.title} ({disaster.affected_location}).",
            category=AuditCategoryChoices.DISASTER
        )

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Returns the currently active disaster event, if any."""
        active_disaster = DisasterEvent.objects.filter(status=DisasterStatusChoices.ACTIVE).first()
        if active_disaster:
            return Response(self.get_serializer(active_disaster).data)
        return Response(None)

    @action(detail=True, methods=['post'], permission_classes=[IsCoordinator])
    @transaction.atomic
    def activate(self, request, pk=None):
        """Coordinators can activate emergency disaster response mode."""
        disaster = self.get_object()
        disaster.status = DisasterStatusChoices.ACTIVE
        disaster.declared_at = timezone.now()
        disaster.declared_by = request.user
        disaster.save()

        for role in ['FOOD_PROVIDER', 'RECIPIENT']:
            send_notification(title='Disaster Emergency Activated', message=f'{disaster.title}: emergency relief is active.', role_target=role, action_url='/dashboard', event_key=f'disaster-act-{disaster.id}-{role}-{int(timezone.now().timestamp())}')

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role='COORDINATOR',
            action='DISASTER_MODE_ACTIVATED',
            details=f"Activated disaster mode: {disaster.title}.",
            category=AuditCategoryChoices.DISASTER
        )

        send_notification(
            title="Disaster Emergency Activated",
            message=f"Emergency disaster mode activated: {disaster.title} ({disaster.affected_location}). Priority routing active.",
            notif_type='alert',
            role_target='COORDINATOR',
            action_url='/admin/dashboard',
            event_key=f"disaster-act-{disaster.id}-{int(timezone.now().timestamp())}"
        )
        send_notification(
            title="Disaster Relief Mobilization",
            message=f"Emergency response mobilized for {disaster.title}. Check available relief transport tasks.",
            notif_type='alert',
            role_target='VOLUNTEER',
            action_url='/volunteer/active',
            event_key=f"disaster-vol-{disaster.id}-{int(timezone.now().timestamp())}"
        )

        return Response({
            'success': True,
            'message': f"Disaster mode active for: {disaster.title}.",
            'disaster': self.get_serializer(disaster).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsCoordinator])
    @transaction.atomic
    def resolve(self, request, pk=None):
        """Coordinators can resolve an emergency disaster event."""
        disaster = self.get_object()
        disaster.status = DisasterStatusChoices.RESOLVED
        disaster.resolved_at = timezone.now()
        disaster.resolved_by = request.user
        disaster.save()
        for role in ['FOOD_PROVIDER', 'RECIPIENT', 'VOLUNTEER']:
            send_notification(title='Disaster Emergency Resolved', message=f'{disaster.title}: emergency response resolved.', role_target=role, action_url='/dashboard', event_key=f'disaster-res-{disaster.id}-{role}-{int(timezone.now().timestamp())}')

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role='COORDINATOR',
            action='DISASTER_MODE_RESOLVED',
            details=f"Resolved disaster response protocol: {disaster.title}.",
            category=AuditCategoryChoices.DISASTER
        )

        send_notification(
            title="Disaster Emergency Resolved",
            message=f"Disaster event '{disaster.title}' resolved. Platform returned to normal community food rescue mode.",
            notif_type='success',
            role_target='COORDINATOR',
            action_url='/admin/dashboard',
            event_key=f"disaster-res-{disaster.id}-{int(timezone.now().timestamp())}"
        )

        return Response({
            'success': True,
            'message': f"Disaster event '{disaster.title}' resolved.",
            'disaster': self.get_serializer(disaster).data
        }, status=status.HTTP_200_OK)

