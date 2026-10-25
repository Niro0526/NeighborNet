from typing import Dict, Any, List
from django.db import transaction
from django.utils import timezone
from apps.intelligence.models import (
    RecommendationBatch, OptimizationRecommendation,
    RecommendationStatusChoices
)
from apps.resources.models import Resource, ResourceStatusChoices
from apps.requests.models import ResourceRequest, RequestStatusChoices
from apps.deliveries.models import (
    Allocation, AllocationStatusChoices,
    DeliveryTask, DeliveryTaskStatusChoices
)
from apps.deliveries.models import DeliveryStatusEvent
from apps.notifications.services import send_notification
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from apps.audit.models import ActivityLog, AuditCategoryChoices

@transaction.atomic
def approve_recommendation_batch(batch_id: str, user) -> RecommendationBatch:
    """Marks an optimization batch as APPROVED by an authorized Coordinator."""
    if not user.is_coordinator or not user.is_active or user.status != 'active':
        raise ValueError('An active approved coordinator is required.')
    batch = RecommendationBatch.objects.select_for_update().filter(id=batch_id).first()
    if not batch:
        raise ValueError(f"Recommendation Batch '{batch_id}' not found.")

    if batch.status not in [RecommendationStatusChoices.PENDING_APPROVAL, RecommendationStatusChoices.DRAFT]:
        raise ValueError('Only a pending plan can be approved and committed.')
    accepted = batch.recommendations.filter(ngo_response='ACCEPTED')
    if batch.solver_status not in ['OPTIMAL', 'FEASIBLE'] or not accepted.exists():
        raise ValueError('At least one NGO must accept a feasible offer before approval.')

    batch.status = RecommendationStatusChoices.APPROVED
    batch.approved_by = user
    batch.approved_at = timezone.now()
    batch.save(update_fields=['status', 'approved_by', 'approved_at'])

    # Update individual recommendations
    accepted.update(status=RecommendationStatusChoices.APPROVED)

    ActivityLog.objects.create(
        user=user,
        user_name=user.name,
        user_role='COORDINATOR',
        action='OPTIMIZATION_PLAN_APPROVED',
        details=f"Coordinator approved distribution plan {batch.id} ({batch.total_allocated_quantity} units).",
        category=AuditCategoryChoices.ADMIN
    )

    return batch

@transaction.atomic
def reject_recommendation_batch(batch_id: str, user, reason: str = "") -> RecommendationBatch:
    """Marks an optimization batch as REJECTED."""
    if not user.is_coordinator or not user.is_active or user.status != 'active':
        raise ValueError('An active approved coordinator is required.')
    batch = RecommendationBatch.objects.select_for_update().filter(id=batch_id).first()
    if not batch:
        raise ValueError(f"Recommendation Batch '{batch_id}' not found.")

    if batch.status == RecommendationStatusChoices.APPLIED:
        raise ValueError("Cannot reject batch that has already been APPLIED.")

    batch.status = RecommendationStatusChoices.REJECTED
    batch.notes = f"{batch.notes}\nRejected: {reason}".strip()
    batch.save(update_fields=['status', 'notes'])

    batch.recommendations.update(status=RecommendationStatusChoices.REJECTED)

    ActivityLog.objects.create(
        user=user,
        user_name=user.name,
        user_role='COORDINATOR',
        action='OPTIMIZATION_PLAN_REJECTED',
        details=f"Coordinator rejected plan {batch.id}: {reason}",
        category=AuditCategoryChoices.ADMIN
    )

    return batch

@transaction.atomic
def apply_recommendation_batch(batch_id: str, user) -> Dict[str, Any]:
    """
    Applies an approved recommendation batch atomically with row locks (select_for_update).
    Re-validates that live inventory hasn't changed or expired.
    Creates authoritative Allocation and DeliveryTask records in PostgreSQL.
    """
    if not user.is_coordinator or not user.is_active or user.status != 'active':
        raise ValueError('An active approved coordinator is required.')
    batch = RecommendationBatch.objects.select_for_update().filter(id=batch_id).first()
    if not batch:
        raise ValueError(f"Recommendation Batch '{batch_id}' not found.")

    if batch.status == RecommendationStatusChoices.APPLIED:
        raise ValueError(f"Batch '{batch_id}' has already been APPLIED.")

    if batch.status != RecommendationStatusChoices.APPROVED:
        raise ValueError(f"Batch '{batch_id}' is in status '{batch.status}' (must be APPROVED to apply).")

    recommendations = list(batch.recommendations.filter(status=RecommendationStatusChoices.APPROVED, ngo_response='ACCEPTED').select_related('resource', 'request', 'assigned_volunteer').order_by('resource_id', 'request_id', 'id'))
    if not recommendations:
        raise ValueError(f"Batch '{batch_id}' contains no recommended allocations to commit.")
    if len({(r.resource_id, r.request_id) for r in recommendations}) != len(recommendations):
        raise ValueError('Duplicate resource/request recommendations in this batch.')

    committed_allocations = []
    created_tasks = []

    # Stable lock order across competing batches; individual claims use the same inventory row.
    locked_resources = {r.pk: r for r in Resource.objects.select_for_update().filter(pk__in=[rec.resource_id for rec in recommendations]).order_by('pk')}
    locked_requests = {q.pk: q for q in ResourceRequest.objects.select_for_update().filter(pk__in=[rec.request_id for rec in recommendations]).order_by('pk')}
    from apps.organizations.models import Organization
    list(Organization.objects.select_for_update().filter(pk__in={r.provider_id for r in locked_resources.values()} | {q.recipient_id for q in locked_requests.values()}).order_by('pk'))
    locked_volunteers = {v.pk: v for v in Volunteer.objects.select_for_update().filter(pk__in=[rec.assigned_volunteer_id for rec in recommendations if rec.assigned_volunteer_id]).order_by('pk')}
    for req in locked_requests.values():
        if not req.allow_partial and abs(sum(rec.allocated_quantity for rec in recommendations if rec.request_id == req.pk)-req.remaining_quantity)>1e-8:
            raise ValueError('Recipient disallows partial fulfillment; regenerate a full plan.')
    assigned = set()

    for rec in recommendations:
        # 1. Lock and re-validate resource
        resource = locked_resources.get(rec.resource_id)
        if not resource:
            raise ValueError(f"Stale plan error: Resource '{rec.resource_id}' no longer exists.")

        if resource.status != ResourceStatusChoices.AVAILABLE:
            raise ValueError(
                f"Stale plan conflict: Resource '{resource.name}' is no longer available (current status: {resource.status})."
            )

        if resource.safe_until and resource.safe_until <= timezone.now():
            raise ValueError('Stale plan: resource has expired.')

        if resource.available_quantity < rec.allocated_quantity:
            raise ValueError(
                f"Concurrent inventory conflict: Resource '{resource.name}' has {resource.available_quantity} available, "
                f"which is less than recommended {rec.allocated_quantity}."
            )

        # 2. Lock and re-validate request
        req = locked_requests.get(rec.request_id)
        if not req:
            raise ValueError(f"Stale plan error: Request '{rec.request_id}' no longer exists.")

        if req.remaining_quantity < rec.allocated_quantity:
            raise ValueError(
                f"Concurrent demand conflict: Request '{req.item_name}' only has {req.remaining_quantity} remaining, "
                f"cannot allocate {rec.allocated_quantity}."
            )
        if req.status not in [RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED]:
            raise ValueError('Stale plan: request is no longer open.')
        if resource.unit != req.unit:
            raise ValueError('Resource and request units must match.')
        import math
        if not math.isfinite(rec.allocated_quantity) or rec.allocated_quantity <= 0 or abs(rec.allocated_quantity-round(rec.allocated_quantity,2))>1e-9 or rec.unit != resource.unit:
            raise ValueError('Invalid recorded recommendation quantity or unit.')
        if rec.created_allocation_id:
            raise ValueError('Recommendation has already been applied.')
        from .eligibility import evaluate_resource_request_eligibility
        eligibility = evaluate_resource_request_eligibility(resource, req)
        if not eligibility.is_eligible:
            raise ValueError('Stale or incompatible recommendation: '+'; '.join(eligibility.reasons_rejected))
        from .volunteer_assignment import volunteer_candidates
        if rec.assigned_volunteer_id:
            candidates, reasons = volunteer_candidates(resource, req)
            candidate = next((c for c in candidates if c['volunteer'].pk == rec.assigned_volunteer_id and c['capacity'] >= rec.allocated_quantity), None)
            if not candidate or rec.assigned_volunteer_id in assigned:
                raise ValueError('Assigned volunteer is no longer feasible or is duplicated in this plan. '+'; '.join(reasons))
            assigned.add(rec.assigned_volunteer_id)
        if resource.is_disaster_relief or req.is_disaster_relief:
            from apps.disasters.models import DisasterEvent
            event_id = resource.disaster_event_id or req.disaster_event_id
            if not DisasterEvent.objects.filter(pk=event_id, status='ACTIVE').exists():
                raise ValueError('Relief allocation requires an active disaster event.')

        # 3. Decrement available inventory and increment allocated
        resource.allocated_quantity = round(resource.allocated_quantity + rec.allocated_quantity, 2)
        if resource.available_quantity <= 0:
            resource.status = ResourceStatusChoices.RESERVED
        resource.save(update_fields=['allocated_quantity', 'status', 'updated_at'])

        # 4. Update request fulfilled and remaining quantity
        req.fulfilled_quantity = round(req.fulfilled_quantity + rec.allocated_quantity, 2)
        if req.remaining_quantity <= 0:
            req.status = RequestStatusChoices.ALLOCATED
        else:
            req.status = RequestStatusChoices.PARTIALLY_ALLOCATED
        req.save(update_fields=['fulfilled_quantity', 'status', 'updated_at'])

        # 5. Create authoritative Allocation record
        alloc = Allocation.objects.create(
            resource=resource,
            request=req,
            allocated_quantity=rec.allocated_quantity,
            status=AllocationStatusChoices.APPROVED,
            created_by=user,
            approved_by=user,
            approved_at=timezone.now(),
        )
        rec.created_allocation = alloc
        rec.status = RecommendationStatusChoices.APPLIED
        rec.save(update_fields=['created_allocation', 'status'])
        committed_allocations.append(alloc)

        # 6. Assign volunteer if designated
        volunteer = locked_volunteers.get(rec.assigned_volunteer_id)
        if volunteer:
            volunteer.status = VolunteerAvailabilityChoices.BUSY
            volunteer.save(update_fields=['status'])

        # 7. Create corresponding DeliveryTask
        task = DeliveryTask.objects.create(
            allocation=alloc,
            resource=resource,
            request=req,
            volunteer=volunteer,
            title=f"Delivery: {resource.name} ({rec.allocated_quantity} {rec.unit})",
            cargo_description=f"{resource.name} - {resource.category}",
            quantity=rec.allocated_quantity,
            unit=rec.unit,
            status=DeliveryTaskStatusChoices.ACCEPTED if volunteer else DeliveryTaskStatusChoices.AVAILABLE,
            priority=req.priority,
            pickup_address=resource.pickup_address or resource.provider.address,
            delivery_address=req.delivery_address or req.recipient.address,
            pickup_contact_phone=resource.provider.contact_phone,
            delivery_contact_phone=req.recipient.contact_phone,
            pickup_time_window=f"{resource.pickup_start.strftime('%H:%M')} - {resource.pickup_end.strftime('%H:%M')}",
            delivery_deadline=req.urgency_deadline,
            is_disaster_mode=resource.is_disaster_relief or req.is_disaster_relief,
            disaster_event=resource.disaster_event or req.disaster_event
        )
        if volunteer:
            task.accepted_at = timezone.now()
            task.assigned_at = task.accepted_at
            task.save(update_fields=['accepted_at','assigned_at'])
        DeliveryStatusEvent.objects.create(delivery_task=task, from_status='INITIAL', to_status=task.status, changed_by=user, notes=f'Coordinator applied plan {batch.id}.')
        for organization in [resource.provider, req.recipient]:
            send_notification(title='Allocation Approved', message=f'{task.title}: {task.status}.', organization=organization, action_url='/dashboard', event_key=f'plan-{alloc.id}-{organization.pk}')
        if volunteer:
            send_notification(title='Delivery Mission Assigned', message=task.title, user=volunteer.user, action_url='/volunteer/active', event_key=f'plan-task-{task.id}')
        created_tasks.append(task)

    # 8. Finalize batch state
    batch.status = RecommendationStatusChoices.APPLIED
    batch.applied_by = user
    batch.applied_at = timezone.now()
    if not batch.approved_by:
        batch.approved_by = user
        batch.approved_at = timezone.now()
    batch.save(update_fields=['status', 'applied_by', 'applied_at', 'approved_by', 'approved_at'])

    ActivityLog.objects.create(
        user=user,
        user_name=user.name,
        user_role='COORDINATOR',
        action='OPTIMIZATION_PLAN_APPLIED',
        details=(
            f"Coordinator atomically committed distribution plan {batch.id}: "
            f"{len(committed_allocations)} allocations and {len(created_tasks)} delivery tasks generated."
        ),
        category=AuditCategoryChoices.ADMIN
    )

    return {
        'success': True,
        'batch_id': batch.id,
        'status': batch.status,
        'allocations_count': len(committed_allocations),
        'delivery_tasks_count': len(created_tasks),
        'allocation_ids': [a.id for a in committed_allocations],
        'task_ids': [t.id for t in created_tasks],
    }
