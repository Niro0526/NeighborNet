from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ResourceRequest, RequestStatusChoices
from .serializers import ResourceRequestSerializer
from common.permissions import IsRecipient, IsCoordinator
from common.permissions import OrganizationResourcePermission
from apps.audit.models import ActivityLog, AuditCategoryChoices

from apps.notifications.services import send_notification

class ResourceRequestViewSet(viewsets.ModelViewSet):
    ordering = ['-created_at', '-id']
    permission_classes = [OrganizationResourcePermission]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_coordinator or self.request.user.is_food_provider:
            return qs
        return qs.filter(recipient__memberships__user=self.request.user, recipient__memberships__is_active=True).distinct()
    queryset = ResourceRequest.objects.all().select_related('recipient')
    serializer_class = ResourceRequestSerializer
    filterset_fields = ['category', 'priority', 'status', 'is_disaster_relief', 'recipient']
    search_fields = ['item_name', 'recipient__name', 'special_instructions']
    ordering_fields = ['created_at', 'urgency_deadline', 'requested_quantity']

    def perform_create(self, serializer):
        req = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            user_name=self.request.user.name,
            user_role='RECIPIENT',
            action='RESOURCE_REQUESTED',
            details=f"Created requisition: {req.item_name} ({req.requested_quantity} {req.unit}) for {req.recipient.name} [{req.priority}].",
            category=AuditCategoryChoices.REQUEST
        )

        send_notification(
            title="Request Created",
            message=f"Requisition registered: {req.item_name} ({req.requested_quantity} {req.unit}).",
            notif_type='info',
            organization=req.recipient,
            action_url='/requests/my-requests',
            event_key=f"req-created-{req.id}"
        )

        if req.priority == 'urgent' or req.is_disaster_relief:
            send_notification(
                title="Urgent Resource Request Alert",
                message=f"Urgent emergency request from {req.recipient.name}: {req.item_name} ({req.requested_quantity} {req.unit}). Priority: {req.priority.upper()}.",
                notif_type='alert',
                role_target='COORDINATOR',
                action_url='/admin/requests',
                event_key=f"req-urgent-{req.id}"
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an open or pending community request."""
        req = self.get_object()
        if req.fulfilled_quantity > 0:
            return Response({'detail': 'Allocated requests cannot be cancelled.'}, status=400)
        is_member = req.recipient.memberships.filter(user=request.user, is_active=True).exists()
        if not (is_member or request.user.is_coordinator):
            return Response({'detail': 'Not authorized to cancel this request.'}, status=status.HTTP_403_FORBIDDEN)

        req.status = RequestStatusChoices.CANCELLED
        req.save()

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role=request.user.get_approved_roles()[0] if request.user.get_approved_roles() else 'USER',
            action='REQUEST_CANCELLED',
            details=f"Requisition cancelled: {req.item_name} ({req.recipient.name}).",
            category=AuditCategoryChoices.REQUEST
        )

        send_notification(
            title="Request Cancelled",
            message=f"Requisition '{req.item_name}' was cancelled.",
            notif_type='warning',
            organization=req.recipient,
            action_url='/requests/my-requests',
            event_key=f"req-cancelled-{req.id}"
        )

        return Response({
            'success': True,
            'message': f"Request '{req.item_name}' cancelled.",
            'request': ResourceRequestSerializer(req).data
        }, status=status.HTTP_200_OK)

