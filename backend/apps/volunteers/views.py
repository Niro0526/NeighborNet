from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Volunteer, VolunteerAvailabilityChoices
from .serializers import VolunteerSerializer
from common.permissions import IsCoordinator, IsVolunteer
from apps.audit.models import ActivityLog, AuditCategoryChoices

from apps.notifications.services import send_notification

class VolunteerViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']

    @action(detail=True, methods=['post'], permission_classes=[IsCoordinator])
    def capabilities(self, request, pk=None):
        from django.db import transaction
        allowed = {'transport_storage', 'travel_speed_kmh', 'vehicleCapacityKg'}
        if set(request.data) - allowed:
            return Response({'detail': 'Only recorded transport storage, speed and capacity can be changed here.'}, status=400)
        with transaction.atomic():
            volunteer = Volunteer.objects.select_for_update().get(pk=self.get_object().pk)
            serializer = self.get_serializer(volunteer, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            ActivityLog.objects.create(user=request.user, user_name=request.user.name, user_role='COORDINATOR', action='COURIER_CAPABILITIES_RECORDED', details=f'Recorded transport capabilities for {volunteer.pk}.', category='ADMIN')
            return Response(serializer.data)

    def get_permissions(self):
        if self.action in ['me', 'toggle_availability']:
            return [IsVolunteer()]
        if self.action == 'create':
            return [IsCoordinator()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        return qs if self.request.user.is_coordinator else qs.filter(user=self.request.user)
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

    @action(detail=False, methods=['get'], permission_classes=[IsCoordinator])
    def pending(self, request):
        """Returns unverified volunteers requiring coordinator approval."""
        pending_vols = Volunteer.objects.filter(verified=False).order_by('-created_at')
        return Response(self.get_serializer(pending_vols, many=True).data)

    @action(detail=False, methods=['post'])
    def toggle_availability(self, request):
        """Toggle online/offline status."""
        volunteer, _ = Volunteer.objects.get_or_create(user=request.user)
        if volunteer.status == VolunteerAvailabilityChoices.BUSY:
            return Response({'detail': 'Complete the active delivery before changing availability.'}, status=400)
        next_status = request.data.get('status') or (VolunteerAvailabilityChoices.OFFLINE if volunteer.status == VolunteerAvailabilityChoices.AVAILABLE else VolunteerAvailabilityChoices.AVAILABLE)
        if next_status not in [VolunteerAvailabilityChoices.AVAILABLE, VolunteerAvailabilityChoices.OFFLINE]:
            return Response({'detail': 'Invalid availability status.'}, status=400)
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

        send_notification(
            title="Courier Credentials Verified",
            message=f"Congratulations {volunteer.user.name}! Your volunteer driver credentials have been verified by {request.user.name}.",
            notif_type='success',
            user=volunteer.user,
            action_url='/volunteer/active',
            event_key=f"vol-verified-{volunteer.id}"
        )

        return Response({
            'success': True,
            'message': f"Volunteer '{volunteer.user.name}' verified.",
            'volunteer': self.get_serializer(volunteer).data
        }, status=status.HTTP_200_OK)

