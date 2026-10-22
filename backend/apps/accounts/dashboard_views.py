from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Q, F

from apps.accounts.models import RoleChoices
from apps.resources.models import Resource, ResourceStatusChoices
from apps.requests.models import ResourceRequest, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from apps.deliveries.models import (
    DeliveryTask,
    DeliveryTaskStatusChoices,
    Allocation,
    AllocationStatusChoices
)
from apps.disasters.models import DisasterEvent, DisasterStatusChoices


from apps.organizations.models import Organization
from apps.audit.models import ActivityLog
from common.permissions import IsCoordinator

from apps.resources.serializers import ResourceSerializer
from apps.requests.serializers import ResourceRequestSerializer
from apps.deliveries.serializers import DeliveryTaskSerializer
from apps.disasters.serializers import DisasterEventSerializer
from apps.volunteers.serializers import VolunteerSerializer
from apps.audit.serializers import ActivityLogSerializer

class UnifiedPersonalDashboardView(views.APIView):
    """
    Personalized Smart Dashboard endpoint (GET /api/v1/dashboard/me/).
    Dynamically responds with authorized modules based on the user's approved roles.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        approved_roles = user.get_approved_roles()

        response_data = {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'assignedRoles': approved_roles,
            },
            'activeDisaster': None,
        }

        # Active Disaster Alert Banner if active
        active_disaster = DisasterEvent.objects.filter(status=DisasterStatusChoices.ACTIVE).first()
        if active_disaster:
            response_data['activeDisaster'] = DisasterEventSerializer(active_disaster).data

        # 1. Food Provider Module
        if user.is_food_provider:
            # Get listings belonging to user's organizations or created by user
            user_org_ids = user.organization_memberships.filter(is_active=True).values_list('organization_id', flat=True)
            my_listings_qs = Resource.objects.filter(
                Q(provider_id__in=user_org_ids) | Q(created_by=user)
            )

            total_donated = DeliveryTask.objects.filter(resource__in=my_listings_qs, status='DELIVERED', unit='kg').aggregate(total=Sum('quantity'))['total'] or 0.0

            provider_tasks=DeliveryTask.objects.filter(resource__in=my_listings_qs)
            pending_pickups = DeliveryTask.objects.filter(
                resource__in=my_listings_qs,
                status__in=[
                    DeliveryTaskStatusChoices.ACCEPTED,
                    DeliveryTaskStatusChoices.ARRIVED_PICKUP
                ]
            ).order_by('delivery_deadline')

            response_data['foodProvider'] = {
                'totalDonatedKg': round(total_donated, 1),
                'activeListingsCount': my_listings_qs.filter(status=ResourceStatusChoices.AVAILABLE).count(),
                'pendingPickupsCount': pending_pickups.count(),
                'completedPickupsCount': provider_tasks.filter(picked_up_at__isnull=False).count(),
                'listings': ResourceSerializer(my_listings_qs.order_by('-created_at')[:6], many=True).data,
                'pendingPickups': DeliveryTaskSerializer(pending_pickups[:5], many=True, context={'request':request}).data,
            }

        # 2. Recipient / NGO Module
        if user.is_recipient:
            user_org_ids = user.organization_memberships.filter(is_active=True).values_list('organization_id', flat=True)
            my_requests_qs = ResourceRequest.objects.filter(
                Q(recipient_id__in=user_org_ids) | Q(created_by=user)
            )

            incoming_shipments = DeliveryTask.objects.filter(
                request__in=my_requests_qs,
                status__in=[
                    DeliveryTaskStatusChoices.ACCEPTED,
                    DeliveryTaskStatusChoices.ARRIVED_PICKUP,
                    DeliveryTaskStatusChoices.PICKED_UP,
                    DeliveryTaskStatusChoices.ARRIVED_DELIVERY,
                ]
            ).order_by('delivery_deadline')[:5]

            available_catalog = Resource.objects.filter(
                status=ResourceStatusChoices.AVAILABLE
            ).order_by('-created_at')[:6]

            response_data['recipient'] = {
                'activeRequestsCount': my_requests_qs.filter(status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED]).count(),
                'incomingDeliveriesCount': incoming_shipments.count(),
                'requests': ResourceRequestSerializer(my_requests_qs.order_by('-created_at')[:6], many=True, context={'request':request}).data,
                'incomingDeliveries': DeliveryTaskSerializer(incoming_shipments, many=True, context={'request':request}).data,
                'availableFoodCatalog': ResourceSerializer(available_catalog, many=True).data,
            }

        # 3. Volunteer Courier Module
        if user.is_volunteer:
            volunteer, _ = Volunteer.objects.get_or_create(user=user)
            active_mission = DeliveryTask.objects.filter(
                volunteer=volunteer,
                status__in=[
                    DeliveryTaskStatusChoices.ACCEPTED,
                    DeliveryTaskStatusChoices.ARRIVED_PICKUP,
                    DeliveryTaskStatusChoices.PICKED_UP,
                    DeliveryTaskStatusChoices.ARRIVED_DELIVERY,
                ]
            ).first()

            available_missions = DeliveryTask.objects.filter(
                status=DeliveryTaskStatusChoices.AVAILABLE
            ).order_by('-priority', 'delivery_deadline')[:6]

            response_data['volunteer'] = {
                'profile': VolunteerSerializer(volunteer, context={'request': request}).data,
                'activeMission': DeliveryTaskSerializer(active_mission, context={'request':request}).data if active_mission else None,
                'availableTasks': DeliveryTaskSerializer(available_missions, many=True, context={'request':request}).data,
                'completedCount': DeliveryTask.objects.filter(volunteer=volunteer, status='DELIVERED').count(),
            }

        # 4. Coordinator Privilege Indicator
        if user.is_coordinator:
            response_data['coordinatorAccess'] = {
                'hasAdminAccess': True,
                'adminWorkspaceUrl': '/admin/dashboard',
            }

        return Response(response_data, status=status.HTTP_200_OK)

class CoordinatorDashboardView(views.APIView):
    """
    Dedicated Coordinator Command Overview endpoint (GET /api/v1/dashboard/admin/).
    Strictly restricted to approved Coordinators.
    """
    permission_classes = [IsCoordinator]

    def get(self, request):
        now = timezone.now()

        # Operational metrics
        total_surplus_kg = Resource.objects.filter(status=ResourceStatusChoices.AVAILABLE, unit='kg').filter(Q(safe_until__isnull=True) | Q(safe_until__gt=now)).aggregate(total=Sum(F('quantity') - F('allocated_quantity')))['total'] or 0.0
        active_requests = ResourceRequest.objects.filter(status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED])
        urgent_requests_count = active_requests.filter(priority='urgent').count()
        volunteers_online_count = Volunteer.objects.filter(status=VolunteerAvailabilityChoices.AVAILABLE).count()
        today_deliveries_count = DeliveryTask.objects.filter(status=DeliveryTaskStatusChoices.DELIVERED, delivered_at__date=now.date()).count()

        # Food at risk of expiry (within next 24 hours)
        expiring_soon = Resource.objects.filter(
            status=ResourceStatusChoices.AVAILABLE,
            safe_until__isnull=False
        ).order_by('safe_until')[:5]

        # Pending approvals
        unverified_orgs = Organization.objects.filter(verified=False).count()
        unverified_volunteers = Volunteer.objects.filter(verified=False).count()

        # Part 5: Coordinator Live Operations Center Metrics
        pending_allocations_count = Allocation.objects.filter(status=AllocationStatusChoices.PENDING).count()
        active_in_transit_tasks = DeliveryTask.objects.filter(
            status__in=[
                DeliveryTaskStatusChoices.ACCEPTED,
                DeliveryTaskStatusChoices.ARRIVED_PICKUP,
                DeliveryTaskStatusChoices.PICKED_UP,
                DeliveryTaskStatusChoices.ARRIVED_DELIVERY,
            ]
        )
        active_deliveries_count = active_in_transit_tasks.count()
        delayed_deliveries_count = active_in_transit_tasks.filter(delivery_deadline__lt=now).count()
        unmet_requests_count = active_requests.count()
        urgent_disaster_requests_count = ResourceRequest.objects.filter(
            Q(priority='urgent') | Q(is_disaster_relief=True),
            status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED]
        ).count()
        disrupted_deliveries_count = DeliveryTask.objects.filter(status=DeliveryTaskStatusChoices.DISRUPTED).count()
        volunteer_declined_count = DeliveryTask.objects.filter(status=DeliveryTaskStatusChoices.DECLINED).count()
        pending_recovery_plans = disrupted_deliveries_count

        # Active disaster
        active_disaster = DisasterEvent.objects.filter(status=DisasterStatusChoices.ACTIVE).first()

        # Recent activities (Live Operational Feed)
        recent_logs = ActivityLog.objects.all().order_by('-timestamp')[:10]

        return Response({
            'kpis': {
                'availableSurplusKg': round(total_surplus_kg, 1),
                'activeRequestsCount': active_requests.count(),
                'urgentRequestsCount': urgent_requests_count,
                'volunteersOnlineCount': volunteers_online_count,
                'deliveriesCompletedToday': today_deliveries_count,
            },
            'pendingApprovals': {
                'unverifiedOrganizations': unverified_orgs,
                'unverifiedVolunteers': unverified_volunteers,
            },
            'liveOperations': {
                'pendingVerifications': {
                    'count': unverified_orgs + unverified_volunteers,
                    'organizations': unverified_orgs,
                    'volunteers': unverified_volunteers,
                    'definition': 'Registered organizations and courier drivers awaiting statutory coordinator verification',
                    'actionUrl': '/admin/approvals',
                    'urgency': 'high' if (unverified_orgs + unverified_volunteers) > 0 else 'low',
                },
                'pendingAllocationApprovals': {
                    'count': pending_allocations_count,
                    'definition': 'Automated or provider-initiated resource allocations awaiting coordinator authorization',
                    'actionUrl': '/admin/matching',
                    'urgency': 'high' if pending_allocations_count > 0 else 'low',
                },
                'activeDeliveries': {
                    'count': active_deliveries_count,
                    'definition': 'Volunteer missions currently in progress (accepted, at pickup, or en route)',
                    'actionUrl': '/admin/map',
                    'urgency': 'medium',
                },
                'delayedDeliveries': {
                    'count': delayed_deliveries_count,
                    'definition': 'Deliveries with recorded deadlines earlier than current timestamp without completed status',
                    'actionUrl': '/admin/map',
                    'urgency': 'urgent' if delayed_deliveries_count > 0 else 'low',
                },
                'unmetRequests': {
                    'count': unmet_requests_count,
                    'definition': 'Registered shelter requisitions currently open or only partially fulfilled',
                    'actionUrl': '/admin/requests',
                    'urgency': 'medium' if unmet_requests_count > 0 else 'low',
                },
                'urgentDisasterRequests': {
                    'count': urgent_disaster_requests_count,
                    'definition': 'Critical requisitions flagged urgent or tagged for active disaster relief response',
                    'actionUrl': '/admin/requests',
                    'urgency': 'urgent' if urgent_disaster_requests_count > 0 else 'low',
                },
                'volunteerDisruptions': {
                    'count': disrupted_deliveries_count + volunteer_declined_count,
                    'disrupted': disrupted_deliveries_count,
                    'declined': volunteer_declined_count,
                    'definition': 'Missions blocked by route hazard or returned to pool following courier cancellation',
                    'actionUrl': '/admin/recovery',
                    'urgency': 'urgent' if disrupted_deliveries_count > 0 else 'low',
                },
                'pendingRecoveryPlans': {
                    'count': pending_recovery_plans,
                    'definition': 'Disrupted delivery corridors requiring human oversight approval to re-route',
                    'actionUrl': '/admin/recovery',
                    'urgency': 'urgent' if pending_recovery_plans > 0 else 'low',
                },
            },
            'expiringResources': ResourceSerializer(expiring_soon, many=True).data,
            'activeDisaster': DisasterEventSerializer(active_disaster).data if active_disaster else None,
            'recentActivity': ActivityLogSerializer(recent_logs, many=True).data,
        }, status=status.HTTP_200_OK)

