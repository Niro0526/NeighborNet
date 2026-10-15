from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Resource, ResourceStatusChoices
from .serializers import ResourceSerializer
from common.permissions import IsFoodProvider, IsCoordinator
from apps.audit.models import ActivityLog, AuditCategoryChoices

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all().select_related('provider')
    serializer_class = ResourceSerializer
    filterset_fields = ['category', 'status', 'is_disaster_relief', 'provider']
    search_fields = ['name', 'provider__name', 'safety_notes']
    ordering_fields = ['created_at', 'safe_until', 'quantity']

    def get_queryset(self):
        qs = super().get_queryset()
        # By default for regular listings, mark and exclude expired food from available listings
        status_param = self.request.query_params.get('status')
        if status_param == 'AVAILABLE':
            # Auto-expire perishable food whose safe-until has passed
            Resource.objects.filter(
                status=ResourceStatusChoices.AVAILABLE,
                safe_until__lt=timezone.now()
            ).update(status=ResourceStatusChoices.EXPIRED)
            return qs.filter(status=ResourceStatusChoices.AVAILABLE)
        return qs

    def perform_create(self, serializer):
        resource = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            user_name=self.request.user.name,
            user_role='FOOD_PROVIDER',
            action='FOOD_SURPLUS_REGISTERED',
            details=f"Listed surplus: {resource.name} ({resource.quantity} {resource.unit}) from {resource.provider.name}.",
            category=AuditCategoryChoices.FOOD
        )

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw a resource lot from active distribution."""
        resource = self.get_object()
        # Security: check membership or coordinator
        is_member = resource.provider.memberships.filter(user=request.user, is_active=True).exists()
        if not (is_member or request.user.is_coordinator):
            return Response({'detail': 'You are not authorized to withdraw this resource.'}, status=status.HTTP_403_FORBIDDEN)

        resource.status = ResourceStatusChoices.WITHDRAWN
        resource.save()

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role=request.user.get_approved_roles()[0] if request.user.get_approved_roles() else 'USER',
            action='RESOURCE_WITHDRAWN',
            details=f"Withdrawn surplus resource: {resource.name}.",
            category=AuditCategoryChoices.FOOD
        )

        return Response({
            'success': True,
            'message': f"Resource '{resource.name}' withdrawn successfully.",
            'resource': ResourceSerializer(resource).data
        }, status=status.HTTP_200_OK)
