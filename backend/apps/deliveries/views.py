from django.db import transaction
import math
from django.db.models import Q, Sum
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    Allocation,
    AllocationStatusChoices,
    DeliveryTask,
    DeliveryTaskStatusChoices,
    DeliveryStatusEvent
)
from .serializers import AllocationSerializer, DeliveryTaskSerializer
from apps.resources.models import Resource, ResourceStatusChoices
from apps.requests.models import ResourceRequest, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from common.permissions import IsCoordinator, IsVolunteer
from apps.audit.models import ActivityLog, AuditCategoryChoices
from apps.notifications.services import send_notification

class AllocationViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_coordinator:
            return qs
        orgs = self.request.user.organization_memberships.filter(is_active=True).values('organization_id')
        scope=Q(pk__in=[])
        if self.request.user.is_food_provider:
            scope |= Q(resource__provider_id__in=orgs)
        if self.request.user.is_recipient:
            scope |= Q(request__recipient_id__in=orgs)
        return qs.filter(scope).distinct()
    queryset = Allocation.objects.all().select_related('resource', 'request', 'resource__provider', 'request__recipient')
    serializer_class = AllocationSerializer
    filterset_fields = ['status', 'resource', 'request']
    ordering_fields = ['created_at', 'allocated_quantity']

    @action(detail=False, methods=['get'])
    def offers(self, request):
        if not request.user.is_recipient:
            raise PermissionDenied('An approved recipient role is required.')
        from apps.intelligence.services.eligibility import evaluate_resource_request_eligibility
        demands=ResourceRequest.objects.filter(recipient__verified=True,recipient__memberships__user=request.user,recipient__memberships__is_active=True,is_disaster_relief=False,status__in=['OPEN','PARTIALLY_ALLOCATED'],urgency_deadline__gt=timezone.now()).select_related('recipient').distinct()
        resources=Resource.objects.filter(provider__verified=True,is_disaster_relief=False,status='AVAILABLE',pickup_end__gt=timezone.now()).select_related('provider')
        offers=[]
        for demand in demands:
            for resource in resources:
                result=evaluate_resource_request_eligibility(resource,demand)
                if result.is_eligible:
                    quantity=math.floor((result.compatible_quantity+1e-9)*100)/100
                    if quantity>0:
                        offers.append({'resourceId':resource.pk,'requestId':demand.pk,'recipientName':demand.recipient.name,'quantity':quantity,'unit':resource.unit})
        return Response(offers)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def accept(self, request, pk=None):
        allocation=Allocation.objects.select_for_update().get(pk=self.get_object().pk)
        if not request.user.is_recipient or not allocation.request.recipient.memberships.filter(user=request.user,is_active=True).exists():
            raise PermissionDenied('Only the receiving NGO may accept this offer.')
        from common.organization_scope import resolve_organization
        resolve_organization(request.user,allocation.request.recipient_id)
        if allocation.ngo_accepted_at or allocation.status not in ['PENDING','APPROVED']:
            return Response({'detail':'Only an unaccepted active allocation can be accepted.'},status=400)
        allocation.ngo_accepted_at=timezone.now()
        allocation.ngo_accepted_by=request.user
        allocation.save(update_fields=['ngo_accepted_at','ngo_accepted_by','updated_at'])
        send_notification(title='NGO Accepted Donation',message=f'{allocation.request.recipient.name} accepted {allocation.allocated_quantity} {allocation.resource.unit} of {allocation.resource.name}.',organization=allocation.resource.provider,action_url='/food/allocations',event_key=f'ngo-accepted-{allocation.pk}')
        return Response(self.get_serializer(allocation).data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Creates a new allocation with row-level locks and atomic inventory reduction.
        Prevents over-allocation and negative inventory.
        """
        resource_id = request.data.get('resource') or request.data.get('resource_id') or request.data.get('resourceId')
        request_id = request.data.get('request') or request.data.get('request_id') or request.data.get('requestId')
        try:
            allocated_quantity = float(request.data.get('allocatedQuantity', request.data.get('allocated_quantity', 0)))
        except (ValueError, TypeError):
            return Response({'detail': 'Invalid allocated quantity.'}, status=status.HTTP_400_BAD_REQUEST)

        if not math.isfinite(allocated_quantity) or allocated_quantity <= 0:
            return Response({'detail': 'Allocated quantity must be strictly greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
        if abs(allocated_quantity-round(allocated_quantity,2))>1e-9:
            return Response({'detail':'Allocated quantity must use at most two decimal places.'},status=400)

        # Lock rows to prevent race conditions
        try:
            resource = Resource.objects.select_for_update().get(id=resource_id)
            res_request = ResourceRequest.objects.select_for_update().get(id=request_id)
        except (Resource.DoesNotExist, ResourceRequest.DoesNotExist):
            return Response({'detail': 'Resource or Resource Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_coordinator and not (
            request.user.is_recipient and res_request.recipient.memberships.filter(user=request.user, is_active=True).exists()
        ):
            raise PermissionDenied('Only the requesting recipient or a coordinator may allocate resources.')
        from common.organization_scope import resolve_organization
        resolve_organization(request.user,res_request.recipient_id)
        if not resource.provider.verified:
            return Response({'detail':'The provider organization must be verified.'},status=400)
        if res_request.urgency_deadline <= timezone.now():
            return Response({'detail':'The request deadline has expired.'},status=400)
        if res_request.status not in ['OPEN', 'PARTIALLY_ALLOCATED'] or allocated_quantity > res_request.remaining_quantity:
            return Response({'detail': 'Allocation exceeds open request demand.'}, status=400)
        if resource.category != res_request.category or resource.unit != res_request.unit:
            return Response({'detail': 'Resource category and unit must match the request.'}, status=400)
        if resource.safe_until and resource.safe_until <= timezone.now():
            return Response({'detail': 'Resource has expired.'}, status=400)
        if resource.is_disaster_relief != res_request.is_disaster_relief or resource.disaster_event_id != res_request.disaster_event_id:
            return Response({'detail': 'Resource and request must use the same operating mode and disaster event.'}, status=400)

        if resource.status != ResourceStatusChoices.AVAILABLE:
            return Response({'detail': f'Resource is not in AVAILABLE state (currently: {resource.status}).'}, status=status.HTTP_400_BAD_REQUEST)

        if allocated_quantity > resource.available_quantity:
            return Response({
                'detail': f'Allocated quantity ({allocated_quantity}) exceeds available resource quantity ({resource.available_quantity}).'
            }, status=status.HTTP_400_BAD_REQUEST)
        if not resource.is_disaster_relief and not request.user.is_coordinator:
            from apps.intelligence.services.eligibility import evaluate_resource_request_eligibility
            match=evaluate_resource_request_eligibility(resource,res_request)
            if not match.is_eligible:
                return Response({'detail':'This offer is no longer eligible.','reasons':match.reasons_rejected},status=400)

        # Update resource allocated quantity
        resource.allocated_quantity = round(resource.allocated_quantity + allocated_quantity, 2)
        if resource.available_quantity <= 0:
            resource.status = ResourceStatusChoices.RESERVED
        resource.save()

        # Update request fulfilled quantity
        res_request.fulfilled_quantity = round(res_request.fulfilled_quantity + allocated_quantity, 2)
        if res_request.remaining_quantity <= 0:
            res_request.status = RequestStatusChoices.ALLOCATED
        else:
            res_request.status = RequestStatusChoices.PARTIALLY_ALLOCATED
        res_request.save()

        # Create Allocation Record
        is_pending = not request.user.is_coordinator
        allocation = Allocation.objects.create(
            resource=resource,
            request=res_request,
            allocated_quantity=allocated_quantity,
            status=AllocationStatusChoices.PENDING if is_pending else AllocationStatusChoices.APPROVED,
            created_by=request.user,
            approved_by=None if is_pending else request.user,
            approved_at=None if is_pending else timezone.now(),
            ngo_accepted_at=timezone.now() if is_pending else None,
            ngo_accepted_by=request.user if is_pending else None,
        )

        # Automatically create Delivery Task for the allocation
        delivery_task = DeliveryTask.objects.create(
            allocation=allocation,
            resource=resource,
            request=res_request,
            title=f"Delivery: {resource.name} ({allocated_quantity} {resource.unit})",
            cargo_description=f"{resource.name} - {resource.category}",
            quantity=allocated_quantity,
            unit=resource.unit,
            status=DeliveryTaskStatusChoices.AVAILABLE,
            priority=res_request.priority,
            pickup_address=resource.pickup_address or resource.provider.address,
            delivery_address=res_request.delivery_address or res_request.recipient.address,
            pickup_contact_phone=resource.provider.contact_phone,
            delivery_contact_phone=res_request.recipient.contact_phone,
            pickup_time_window=f"{resource.pickup_start.strftime('%H:%M')} - {resource.pickup_end.strftime('%H:%M')}",
            delivery_deadline=res_request.urgency_deadline,
            is_disaster_mode=resource.is_disaster_relief or res_request.is_disaster_relief,
            disaster_event=resource.disaster_event or res_request.disaster_event
        )

        # Record initial status event
        DeliveryStatusEvent.objects.create(
            delivery_task=delivery_task,
            from_status='INITIAL',
            to_status=DeliveryTaskStatusChoices.AVAILABLE,
            changed_by=request.user,
            notes=f"Delivery task opened for allocation {allocation.id}."
        )

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role=request.user.get_approved_roles()[0] if request.user.get_approved_roles() else 'USER',
            action='RESOURCE_ALLOCATED',
            details=f"Allocated {allocated_quantity} {resource.unit} of {resource.name} to {res_request.recipient.name}. Task {delivery_task.id} opened.",
            category=AuditCategoryChoices.FOOD
        )

        # Dispatch persisted business notifications
        send_notification(
            title="NGO Accepted Donation" if is_pending else "Resource Allocated",
            message=f"{res_request.recipient.name} accepted {allocated_quantity} {resource.unit} of {resource.name}; awaiting coordinator approval." if is_pending else f"Allocated {allocated_quantity} {resource.unit} of {resource.name} to {res_request.recipient.name}.",
            notif_type='success',
            organization=resource.provider,
            action_url='/food/allocations',
            event_key=f"alloc-prov-{allocation.id}"
        )
        send_notification(
            title="Resource Matched & Allocated",
            message=f"Allocated {allocated_quantity} {resource.unit} of {resource.name} from {resource.provider.name}.",
            notif_type='success',
            organization=res_request.recipient,
            action_url='/requests/my-requests',
            event_key=f"alloc-recip-{allocation.id}"
        )
        if is_pending:
            send_notification(
                title="Pending Allocation Approval",
                message=f"Allocation of {allocated_quantity} {resource.unit} for {res_request.recipient.name} requires coordinator approval.",
                notif_type='info',
                role_target='COORDINATOR',
                action_url='/admin/matching',
                event_key=f"alloc-pend-{allocation.id}"
            )
        else:
            send_notification(
                title="New Delivery Mission Available",
                message=f"New courier mission available: {delivery_task.title} for {res_request.recipient.name}.",
                notif_type='info',
                role_target='VOLUNTEER',
                action_url='/volunteer/tasks',
                event_key=f"task-avail-{delivery_task.id}"
            )

        serializer = self.get_serializer(allocation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsCoordinator])
    @transaction.atomic
    def approve(self, request, pk=None):
        allocation = Allocation.objects.select_for_update().get(pk=self.get_object().pk)
        if allocation.status != AllocationStatusChoices.PENDING:
            return Response({'detail': 'Only pending allocations can be approved.'}, status=400)
        resource=Resource.objects.select_for_update().get(pk=allocation.resource_id)
        demand=ResourceRequest.objects.select_for_update().get(pk=allocation.request_id)
        if not resource.provider.verified or not demand.recipient.verified:
            return Response({'detail':'Both organizations must remain verified.'},status=400)
        if (resource.safe_until and resource.safe_until<=timezone.now()) or demand.urgency_deadline<=timezone.now() or resource.status in ['EXPIRED','WITHDRAWN']:
            return Response({'detail':'This allocation is no longer safe or within its delivery deadline.'},status=400)
        allocation.status = AllocationStatusChoices.APPROVED
        allocation.approved_by = request.user
        allocation.approved_at = timezone.now()
        allocation.save()
        send_notification(title='New Delivery Mission Available', message=f'Delivery approved: {allocation.delivery_task.title}', role_target='VOLUNTEER', action_url='/volunteer/tasks', event_key=f'task-avail-{allocation.delivery_task.id}')

        # Send approval notifications
        send_notification(
            title="Allocation Approved",
            message=f"Coordinator approved allocation of {allocation.allocated_quantity} {allocation.resource.unit} of {allocation.resource.name}.",
            notif_type='success',
            organization=allocation.resource.provider,
            action_url='/food/pickups',
            event_key=f"alloc-appr-p-{allocation.id}"
        )
        send_notification(
            title="Allocation Approved",
            message=f"Coordinator approved your request allocation for {allocation.resource.name}.",
            notif_type='success',
            organization=allocation.request.recipient,
            action_url='/requests/my-requests',
            event_key=f"alloc-appr-r-{allocation.id}"
        )

        return Response({'success': True, 'allocation': self.get_serializer(allocation).data})

class DeliveryTaskViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        raise PermissionDenied('Delivery tasks are created only through approved allocations.')

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_coordinator:
            return qs
        orgs = user.organization_memberships.filter(is_active=True).values('organization_id')
        scope = Q(pk__in=[])
        if user.is_food_provider:
            scope |= Q(resource__provider_id__in=orgs)
        if user.is_recipient:
            scope |= Q(request__recipient_id__in=orgs)
        if user.is_volunteer:
            pool = Q(status='AVAILABLE', allocation__status='APPROVED', delivery_deadline__gt=timezone.now()) & (Q(resource__safe_until__isnull=True) | Q(resource__safe_until__gt=timezone.now()))
            scope |= Q(volunteer__user=user) | pool
        return qs.filter(scope).distinct()

    def get_object(self):
        task = super().get_object()
        if self.request.method == 'POST':
            # Called inside atomic transition methods; lock the task before checking state.
            task = DeliveryTask.objects.select_for_update().get(pk=task.pk)
            user = self.request.user
            if self.action == 'accept':
                if not user.is_volunteer or not task.allocation or task.allocation.status != 'APPROVED':
                    raise PermissionDenied('Only approved volunteers may claim approved allocations.')
                if task.status != 'AVAILABLE' and not (task.status == 'DISRUPTED' and task.volunteer_id and task.volunteer.user_id == user.pk):
                    raise PermissionDenied('This task is already assigned.')
            else:
                courier = user.is_volunteer and task.volunteer_id and task.volunteer.user_id == user.pk
                recipient = self.action in ['delivered', 'complete', 'confirm_receipt'] and user.is_recipient and task.request.recipient.memberships.filter(user=user, is_active=True).exists()
                provider = self.action in ['picked_up', 'pickup'] and user.is_food_provider and task.resource.provider.memberships.filter(user=user, is_active=True).exists()
                if not (courier or recipient or provider or user.is_coordinator):
                    raise PermissionDenied('Only the assigned courier, receiving organization, or coordinator may perform this action.')
        return task
    queryset = DeliveryTask.objects.all().select_related('resource', 'request', 'volunteer', 'volunteer__user').prefetch_related('status_events')
    serializer_class = DeliveryTaskSerializer
    filterset_fields = ['status', 'priority', 'is_disaster_mode', 'volunteer']
    search_fields = ['title', 'cargo_description', 'pickup_address', 'delivery_address']
    ordering_fields = ['created_at', 'delivery_deadline', 'priority']

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    @transaction.atomic
    def accept(self, request, pk=None):
        """Volunteer accepts an available delivery task."""
        task = self.get_object()
        if not task.can_transition_to(DeliveryTaskStatusChoices.ACCEPTED):
            return Response({'detail': f'Cannot accept task from status {task.status}.'}, status=status.HTTP_400_BAD_REQUEST)
        if task.delivery_deadline <= timezone.now() or (task.resource.safe_until and task.resource.safe_until <= timezone.now()):
            return Response({'detail': 'The delivery window or food safety deadline has expired.'}, status=400)

        # Get or create volunteer profile for requesting user
        volunteer, _ = Volunteer.objects.get_or_create(user=request.user)
        volunteer = Volunteer.objects.select_for_update().get(pk=volunteer.pk)
        is_resume = task.status == 'DISRUPTED' and task.volunteer_id == volunteer.pk
        if (volunteer.status != VolunteerAvailabilityChoices.AVAILABLE and not is_resume) or not volunteer.verified:
            return Response({'detail': 'A verified, available courier profile is required.'}, status=400)
        if task.unit == 'kg' and task.quantity > volunteer.vehicle_capacity_kg:
            return Response({'detail': 'Task exceeds vehicle capacity.'}, status=400)
        previous_status = task.status
        task.volunteer = volunteer
        task.status = DeliveryTaskStatusChoices.ACCEPTED
        task.accepted_at = task.accepted_at if is_resume and task.accepted_at else timezone.now()
        if not is_resume:
            task.assigned_at = task.accepted_at
        task.save()

        volunteer.status = VolunteerAvailabilityChoices.BUSY
        volunteer.save()

        # Append-only status event
        DeliveryStatusEvent.objects.create(
            delivery_task=task,
            from_status=previous_status,
            to_status=DeliveryTaskStatusChoices.ACCEPTED,
            changed_by=request.user,
            notes=f"Courier {request.user.name} accepted mission."
        )

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role='VOLUNTEER',
            action='TASK_ACCEPTED',
            details=f"Volunteer {request.user.name} accepted mission {task.title}.",
            category=AuditCategoryChoices.DELIVERY
        )

        # Notifications
        send_notification(
            title="Mission Accepted",
            message=f"You accepted delivery: {task.title}. Proceed to pickup location.",
            notif_type='info',
            user=request.user,
            action_url='/volunteer/active',
            event_key=f"task-acc-vol-{task.id}"
        )
        send_notification(
            title="Courier Assigned for Pickup",
            message=f"Courier {request.user.name} accepted pickup for {task.cargo_description}.",
            notif_type='info',
            organization=task.resource.provider,
            action_url='/food/pickups',
            event_key=f"task-acc-prov-{task.id}"
        )
        send_notification(
            title="Courier Assigned",
            message=f"Courier {request.user.name} is en route to collect your items.",
            notif_type='info',
            organization=task.request.recipient,
            action_url='/requests/my-requests',
            event_key=f"task-acc-rec-{task.id}"
        )

        return Response({'success': True, 'task': self.get_serializer(task).data})

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    @transaction.atomic
    def arrive_pickup(self, request, pk=None):
        """Courier arrives at donor facility."""
        task = self.get_object()
        if not task.can_transition_to(DeliveryTaskStatusChoices.ARRIVED_PICKUP):
            return Response({'detail': f'Invalid transition from {task.status} to ARRIVED_PICKUP.'}, status=status.HTTP_400_BAD_REQUEST)

        prev_status = task.status
        task.status = DeliveryTaskStatusChoices.ARRIVED_PICKUP
        task.arrived_pickup_at = timezone.now()
        task.save()

        DeliveryStatusEvent.objects.create(
            delivery_task=task,
            from_status=prev_status,
            to_status=DeliveryTaskStatusChoices.ARRIVED_PICKUP,
            changed_by=request.user,
            notes="Courier arrived at donor facility."
        )

        send_notification(
            title="Courier Arrived for Pickup",
            message=f"Courier {request.user.name} has arrived at your facility for {task.cargo_description}.",
            notif_type='info',
            organization=task.resource.provider,
            action_url='/food/pickups',
            event_key=f"task-arr-pick-{task.id}"
        )

        return Response({'success': True, 'task': self.get_serializer(task).data})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def picked_up(self, request, pk=None):
        """Courier confirms items picked up."""
        task = self.get_object()
        if not task.can_transition_to(DeliveryTaskStatusChoices.PICKED_UP):
            return Response({'detail': f'Invalid transition from {task.status} to PICKED_UP.'}, status=status.HTTP_400_BAD_REQUEST)

        prev_status = task.status
        task.status = DeliveryTaskStatusChoices.PICKED_UP
        task.picked_up_at = timezone.now()
        task.save()

        # Update resource status to COLLECTED
        if task.resource:
            task.resource = Resource.objects.select_for_update().get(pk=task.resource_id)
            uncollected = task.resource.delivery_tasks.filter(picked_up_at__isnull=True).exclude(status='CANCELLED').exists() or task.resource.personal_claims.filter(status__in=['PENDING', 'APPROVED', 'ASSIGNED']).exists()
            task.resource.status = (ResourceStatusChoices.AVAILABLE if task.resource.available_quantity > 0 else ResourceStatusChoices.RESERVED if uncollected else ResourceStatusChoices.COLLECTED)
            task.resource.save()

        DeliveryStatusEvent.objects.create(
            delivery_task=task,
            from_status=prev_status,
            to_status=DeliveryTaskStatusChoices.PICKED_UP,
            changed_by=request.user,
            notes="Goods picked up and verified. En route to destination."
        )

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role='VOLUNTEER',
            action='FOOD_PICKED_UP',
            details=f"Courier picked up {task.cargo_description} from donor kitchen.",
            category=AuditCategoryChoices.DELIVERY
        )

        send_notification(
            title="Pickup Completed",
            message=f"Pickup confirmed for {task.cargo_description}.",
            notif_type='success',
            organization=task.resource.provider,
            action_url='/food/pickups',
            event_key=f"task-pick-prov-{task.id}"
        )
        send_notification(
            title="Shipment En Route",
            message=f"Courier {request.user.name} has collected your items and is transporting them to your center.",
            notif_type='info',
            organization=task.request.recipient,
            action_url='/requests/my-requests',
            event_key=f"task-pick-rec-{task.id}"
        )

        return Response({'success': True, 'task': self.get_serializer(task).data})

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    @transaction.atomic
    def arrive_delivery(self, request, pk=None):
        """Courier arrives at destination shelter."""
        task = self.get_object()
        if not task.can_transition_to(DeliveryTaskStatusChoices.ARRIVED_DELIVERY):
            return Response({'detail': f'Invalid transition from {task.status} to ARRIVED_DELIVERY.'}, status=status.HTTP_400_BAD_REQUEST)

        prev_status = task.status
        task.status = DeliveryTaskStatusChoices.ARRIVED_DELIVERY
        task.arrived_delivery_at = timezone.now()
        task.save()

        DeliveryStatusEvent.objects.create(
            delivery_task=task,
            from_status=prev_status,
            to_status=DeliveryTaskStatusChoices.ARRIVED_DELIVERY,
            changed_by=request.user,
            notes="Courier arrived at destination shelter."
        )

        send_notification(
            title="Courier Arrived at Destination",
            message=f"Courier {request.user.name} has arrived with your delivery.",
            notif_type='info',
            organization=task.request.recipient,
            action_url='/requests/my-requests',
            event_key=f"task-arr-del-{task.id}"
        )

        return Response({'success': True, 'task': self.get_serializer(task).data})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def delivered(self, request, pk=None):
        """Courier or Recipient confirms final delivery delivery."""
        task = self.get_object()
        if not task.can_transition_to(DeliveryTaskStatusChoices.DELIVERED):
            return Response({'detail': f'Cannot confirm delivery from status {task.status}. Must be picked up first.'}, status=status.HTTP_400_BAD_REQUEST)

        prev_status = task.status
        task.status = DeliveryTaskStatusChoices.DELIVERED
        task.delivered_at = timezone.now()
        task.save()

        if task.allocation:
            task.allocation.status = AllocationStatusChoices.FULFILLED
            task.allocation.save()

        if task.request:
            task.request = ResourceRequest.objects.select_for_update().get(pk=task.request_id)
            delivered_quantity = DeliveryTask.objects.filter(request=task.request, status='DELIVERED').aggregate(total=Sum('quantity'))['total'] or 0
            task.request.status = RequestStatusChoices.FULFILLED if delivered_quantity >= task.request.requested_quantity else (RequestStatusChoices.ALLOCATED if task.request.remaining_quantity <= 0 else RequestStatusChoices.PARTIALLY_ALLOCATED)
            task.request.save()

        if task.volunteer:
            task.volunteer = Volunteer.objects.select_for_update().get(pk=task.volunteer_id)
            task.volunteer.completed_deliveries_count += 1
            task.volunteer.status = VolunteerAvailabilityChoices.AVAILABLE
            task.volunteer.save()

        DeliveryStatusEvent.objects.create(
            delivery_task=task,
            from_status=prev_status,
            to_status=DeliveryTaskStatusChoices.DELIVERED,
            changed_by=request.user,
            notes="Safe delivery successfully verified and completed."
        )

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role=request.user.get_approved_roles()[0] if request.user.get_approved_roles() else 'USER',
            action='DELIVERY_COMPLETED',
            details=f"Safe delivery confirmed for {task.title} to {task.delivery_address}.",
            category=AuditCategoryChoices.DELIVERY
        )

        # Notify volunteer, provider, recipient
        if task.volunteer:
            send_notification(
                title="Delivery Completed",
                message=f"Mission completed! Safe delivery confirmed for {task.title}.",
                notif_type='success',
                user=task.volunteer.user,
                action_url='/volunteer/active',
                event_key=f"task-deliv-vol-{task.id}"
            )
        send_notification(
            title="Delivery Completed",
            message=f"Your donation of {task.cargo_description} was delivered to {task.request.recipient.name}. NGO receipt confirmation is pending.",
            notif_type='success',
            organization=task.resource.provider,
            action_url='/food/allocations',
            event_key=f"task-deliv-prov-{task.id}"
        )
        send_notification(
            title="Delivery Completed",
            message=f"Delivery recorded for {task.cargo_description}. Please confirm receipt after checking the goods.",
            notif_type='success',
            organization=task.request.recipient,
            action_url='/requests/my-requests',
            event_key=f"task-deliv-rec-{task.id}"
        )

        return Response({'success': True, 'task': self.get_serializer(task).data})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def confirm_receipt(self, request, pk=None):
        task=self.get_object()
        if not request.user.is_recipient or not task.request.recipient.memberships.filter(user=request.user,is_active=True).exists():
            raise PermissionDenied('Only the receiving NGO may confirm receipt.')
        from common.organization_scope import resolve_organization
        resolve_organization(request.user,task.request.recipient_id)
        if task.status!='DELIVERED' or not task.delivered_at:
            return Response({'detail':'Receipt requires a recorded delivery first.'},status=400)
        if task.receipt_confirmed_at:
            return Response({'detail':'Receipt has already been confirmed.'},status=400)
        task.receipt_confirmed_at=timezone.now()
        task.receipt_confirmed_by=request.user
        task.save(update_fields=['receipt_confirmed_at','receipt_confirmed_by','updated_at'])
        ActivityLog.objects.create(user=request.user,user_name=request.user.name,user_role='RECIPIENT',action='NGO_RECEIPT_CONFIRMED',details=f'{task.request.recipient.name} confirmed receipt of {task.quantity} {task.unit} for task {task.pk}.',category=AuditCategoryChoices.DELIVERY)
        for organization in [task.resource.provider,task.request.recipient]:
            send_notification(title='NGO Receipt Confirmed',message=f'{task.request.recipient.name} confirmed receipt of {task.quantity} {task.unit} of {task.resource.name}.',organization=organization,action_url='/food/allocations' if organization.pk==task.resource.provider_id else '/requests/deliveries',event_key=f'receipt-{task.pk}-{organization.pk}')
        send_notification(title='NGO Receipt Confirmed',message=f'{task.request.recipient.name} confirmed receipt for task {task.pk}.',role_target='COORDINATOR',action_url='/admin/allocations',event_key=f'receipt-coord-{task.pk}')
        if task.volunteer_id and task.volunteer.user.is_volunteer:
            send_notification(title='NGO Receipt Confirmed',message=f'{task.request.recipient.name} confirmed receipt for task {task.pk}.',user=task.volunteer.user,action_url='/volunteer/tasks',event_key=f'receipt-courier-{task.pk}')
        return Response({'task':self.get_serializer(task).data})

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    def arrived_pickup(self, request, pk=None):
        return self.arrive_pickup(request, pk)

    @action(detail=True, methods=['post'])
    def pickup(self, request, pk=None):
        return self.picked_up(request, pk)

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    def arrived_delivery(self, request, pk=None):
        return self.arrive_delivery(request, pk)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        return self.delivered(request, pk)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def disrupt(self, request, pk=None):
        """Report route disruption or hazard."""
        task = self.get_object()
        if not task.can_transition_to(DeliveryTaskStatusChoices.DISRUPTED):
            return Response({'detail': 'This task cannot be disrupted from its current state.'}, status=400)
        reason = request.data.get('reason', 'Road disruption or flood inundation encountered.')
        prev_status = task.status
        task.status = DeliveryTaskStatusChoices.DISRUPTED
        task.disruption_reason = reason
        task.save()

        DeliveryStatusEvent.objects.create(
            delivery_task=task,
            from_status=prev_status,
            to_status=DeliveryTaskStatusChoices.DISRUPTED,
            changed_by=request.user,
            notes=reason
        )

        ActivityLog.objects.create(
            user=request.user,
            user_name=request.user.name,
            user_role=request.user.get_approved_roles()[0] if request.user.get_approved_roles() else 'USER',
            action='ROUTE_DISRUPTED',
            details=f"Delivery task {task.id} reported disruption: {reason}.",
            category=AuditCategoryChoices.DISASTER
        )

        # Alert Coordinators
        send_notification(
            title="Route Disrupted Alert",
            message=f"Delivery {task.id} encountered disruption: {reason}. Intervention required.",
            notif_type='alert',
            role_target='COORDINATOR',
            action_url='/admin/matching',
            event_key=f"task-disrupt-{task.id}-{int(timezone.now().timestamp())}"
        )

        return Response({'success': True, 'task': self.get_serializer(task).data})

