from django.db import transaction
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
    queryset = Allocation.objects.all().select_related('resource', 'request', 'resource__provider', 'request__recipient')
    serializer_class = AllocationSerializer
    filterset_fields = ['status', 'resource', 'request']
    ordering_fields = ['created_at', 'allocated_quantity']

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

        if allocated_quantity <= 0:
            return Response({'detail': 'Allocated quantity must be strictly greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

        # Lock rows to prevent race conditions
        try:
            resource = Resource.objects.select_for_update().get(id=resource_id)
            res_request = ResourceRequest.objects.select_for_update().get(id=request_id)
        except (Resource.DoesNotExist, ResourceRequest.DoesNotExist):
            return Response({'detail': 'Resource or Resource Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if resource.status != ResourceStatusChoices.AVAILABLE:
            return Response({'detail': f'Resource is not in AVAILABLE state (currently: {resource.status}).'}, status=status.HTTP_400_BAD_REQUEST)

        if allocated_quantity > resource.available_quantity:
            return Response({
                'detail': f'Allocated quantity ({allocated_quantity}) exceeds available resource quantity ({resource.available_quantity}).'
            }, status=status.HTTP_400_BAD_REQUEST)

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
            approved_by=None if is_pending else request.user
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
            pickup_address=resource.provider.address,
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
            title="Resource Allocated",
            message=f"Allocated {allocated_quantity} {resource.unit} of {resource.name} to {res_request.recipient.name}.",
            notif_type='success',
            organization=resource.provider,
            action_url='/food/pickups',
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
                message=f"New courier mission available: {delivery_task.title}. Destination: {delivery_task.delivery_address}.",
                notif_type='info',
                role_target='VOLUNTEER',
                action_url='/volunteer/tasks',
                event_key=f"task-avail-{delivery_task.id}"
            )

        serializer = self.get_serializer(allocation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsCoordinator])
    def approve(self, request, pk=None):
        allocation = self.get_object()
        allocation.status = AllocationStatusChoices.APPROVED
        allocation.approved_by = request.user
        allocation.save()

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
    queryset = DeliveryTask.objects.all().select_related('resource', 'request', 'volunteer', 'volunteer__user').prefetch_related('status_events')
    serializer_class = DeliveryTaskSerializer
    filterset_fields = ['status', 'priority', 'is_disaster_mode', 'volunteer']
    search_fields = ['title', 'cargo_description', 'pickup_address', 'delivery_address']
    ordering_fields = ['created_at', 'delivery_deadline', 'priority']

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    def accept(self, request, pk=None):
        """Volunteer accepts an available delivery task."""
        task = self.get_object()
        if not task.can_transition_to(DeliveryTaskStatusChoices.ACCEPTED):
            return Response({'detail': f'Cannot accept task from status {task.status}.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create volunteer profile for requesting user
        volunteer, _ = Volunteer.objects.get_or_create(user=request.user)
        task.volunteer = volunteer
        task.status = DeliveryTaskStatusChoices.ACCEPTED
        task.accepted_at = timezone.now()
        task.save()

        volunteer.status = VolunteerAvailabilityChoices.BUSY
        volunteer.save()

        # Append-only status event
        DeliveryStatusEvent.objects.create(
            delivery_task=task,
            from_status=DeliveryTaskStatusChoices.AVAILABLE,
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

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
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
            task.resource.status = ResourceStatusChoices.COLLECTED
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
            task.request.status = RequestStatusChoices.FULFILLED
            task.request.save()

        if task.volunteer:
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
            message=f"Your donation of {task.cargo_description} was delivered to {task.delivery_address}.",
            notif_type='success',
            organization=task.resource.provider,
            action_url='/food/history',
            event_key=f"task-deliv-prov-{task.id}"
        )
        send_notification(
            title="Delivery Completed",
            message=f"Resources {task.cargo_description} successfully received.",
            notif_type='success',
            organization=task.request.recipient,
            action_url='/requests/history',
            event_key=f"task-deliv-rec-{task.id}"
        )

        return Response({'success': True, 'task': self.get_serializer(task).data})

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    def arrived_pickup(self, request, pk=None):
        return self.arrive_pickup(request, pk)

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    def pickup(self, request, pk=None):
        return self.picked_up(request, pk)

    @action(detail=True, methods=['post'], permission_classes=[IsVolunteer])
    def arrived_delivery(self, request, pk=None):
        return self.arrive_delivery(request, pk)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        return self.delivered(request, pk)

    @action(detail=True, methods=['post'])
    def disrupt(self, request, pk=None):
        """Report route disruption or hazard."""
        task = self.get_object()
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

