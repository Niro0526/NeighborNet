from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Volunteer, VolunteerAvailabilityChoices
from .serializers import VolunteerSerializer
from common.permissions import IsCoordinator, IsVolunteer
from apps.audit.models import ActivityLog, AuditCategoryChoices

class VolunteerViewSet(viewsets.ModelViewSet):
    queryset = Volunteer.objects.all().select_related('user')
    serializer_class = VolunteerSerializer
    filterset_fields = ['status', 'vehicle_type', 'verified']
    search_fields = ['user__full_name', 'user__email', 'service_area']
    ordering_fields = ['completed_deliveries_count', 'rating', 'created_at']

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get or initialize the volunteer profile for the authenticated user."""
        volunteer, created = Volunteer.objects.get_or_create(
            user=request.user,
            defaults={
                'status': VolunteerAvailabilityChoices.AVAILABLE,
                'vehicle_type': 'motorcycle',
                'vehicle_capacity_kg': 25.0,
                'service_area': 'Moratuwa & Colombo South',
                'verified': request.user.is_coordinator
            }
        )
        serializer = self.get_serializer(volunteer)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def toggle_availability(self, request):
        """Toggle online/offline status."""
        volunteer, _ = Volunteer.objects.get_or_create(user=request.user)
        next_status = VolunteerAvailabilityChoices.OFFLINE if volunteer.status == VolunteerAvailabilityChoices.AVAILABLE else VolunteerAvailabilityChoices.AVAILABLE
        volunteer.status = next_status
        volunteer.save()

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role='VOLUNTEER',
            action='VOLUNTEER_AVAILABILITY_TOGGLED',
            details=f"Courier availability switched to {next_status}.",
            category=AuditCategoryChoices.DELIVERY
        )

        return Response({
            'success': True,
            'status': volunteer.status,
            'volunteer': self.get_serializer(volunteer).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsCoordinator])
    def verify(self, request, pk=None):
        """Coordinator verification of volunteer driver's license and readiness."""
        volunteer = self.get_object()
        volunteer.verified = True
        volunteer.verified_by = request.user
        volunteer.verified_at = timezone.now()
        volunteer.save()

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role='COORDINATOR',
            action='VOLUNTEER_VERIFIED',
            details=f"Coordinator verified courier credentials for {volunteer.user.name}.",
            category=AuditCategoryChoices.ADMIN
        )

        return Response({
            'success': True,
            'message': f"Volunteer '{volunteer.user.name}' verified.",
            'volunteer': self.get_serializer(volunteer).data
        }, status=status.HTTP_200_OK)
