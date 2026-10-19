from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Organization, OrganizationMembership, MembershipRoleChoices
from .serializers import OrganizationSerializer, OrganizationMembershipSerializer
from common.permissions import IsCoordinator
from apps.audit.models import ActivityLog, AuditCategoryChoices

from apps.notifications.services import send_notification

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filterset_fields = ['type', 'verified', 'city']
    search_fields = ['name', 'address', 'city', 'description']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['verify', 'pending']:
            return [IsCoordinator()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        org = serializer.save()
        # Automatically make the creator the owner/admin of the organization
        OrganizationMembership.objects.create(
            organization=org,
            user=self.request.user,
            role=MembershipRoleChoices.OWNER
        )
        ActivityLog.objects.create(
            user=self.request.user,
            user_name=self.request.user.name,
            user_role=self.request.user.get_approved_roles()[0] if self.request.user.get_approved_roles() else 'USER',
            action='ORGANIZATION_CREATED',
            details=f"Registered organization: {org.name} ({org.type}).",
            category=AuditCategoryChoices.ADMIN
        )

        # Notify Coordinators
        send_notification(
            title="Pending Organization Verification",
            message=f"New organization registered: {org.name} ({org.type}). Awaiting verification.",
            notif_type='info',
            role_target='COORDINATOR',
            action_url='/admin/approvals',
            event_key=f"org-pending-{org.id}"
        )

    @action(detail=False, methods=['get'], permission_classes=[IsCoordinator])
    def pending(self, request):
        """Returns unverified organizations requiring coordinator approval."""
        pending_orgs = Organization.objects.filter(verified=False).order_by('-created_at')
        return Response(self.get_serializer(pending_orgs, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsCoordinator])
    def verify(self, request, pk=None):
        """Coordinators can approve and verify organizations."""
        org = self.get_object()
        org.verified = True
        org.verified_by = request.user
        org.verified_at = timezone.now()
        org.save()

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role='COORDINATOR',
            action='ORGANIZATION_VERIFIED',
            details=f"Coordinator verified organization {org.name} (Reg: {org.registration_number or 'N/A'}).",
            category=AuditCategoryChoices.ADMIN
        )

        # Notify organization members
        send_notification(
            title="Organization Verified",
            message=f"Congratulations! Organization '{org.name}' has been verified by {request.user.name}.",
            notif_type='success',
            organization=org,
            action_url='/profile',
            event_key=f"org-verified-{org.id}"
        )

        return Response({
            'success': True,
            'message': f"Organization '{org.name}' verified successfully.",
            'organization': OrganizationSerializer(org).data
        }, status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'])
    def my_organizations(self, request):
        """Returns organizations where current user has membership."""
        user_orgs = Organization.objects.filter(
            memberships__user=request.user,
            memberships__is_active=True
        ).distinct()
        serializer = self.get_serializer(user_orgs, many=True)
        return Response(serializer.data)
