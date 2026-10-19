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
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from apps.audit.models import ActivityLog, AuditCategoryChoices

@transaction.atomic
def approve_recommendation_batch(batch_id: str, user) -> RecommendationBatch:
    """Marks an optimization batch as APPROVED by an authorized Coordinator."""
    batch = RecommendationBatch.objects.select_for_update().filter(id=batch_id).first()
    if not batch:
        raise ValueError(f"Recommendation Batch '{batch_id}' not found.")

    if batch.status == RecommendationStatusChoices.APPLIED:
        raise ValueError("Cannot modify batch that has already been APPLIED.")

    batch.status = RecommendationStatusChoices.APPROVED
    batch.approved_by = user
    batch.approved_at = timezone.now()
    batch.save(update_fields=['status', 'approved_by', 'approved_at'])

    # Update individual recommendations
    batch.recommendations.update(status=RecommendationStatusChoices.APPROVED)

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
    batch = RecommendationBatch.objects.select_for_update().filter(id=batch_id).first()
    if not batch:
        raise ValueError(f"Recommendation Batch '{batch_id}' not found.")

    if batch.status == RecommendationStatusChoices.APPLIED:
        raise ValueError(f"Batch '{batch_id}' has already been APPLIED.")

    if batch.status not in (RecommendationStatusChoices.APPROVED, RecommendationStatusChoices.PENDING_APPROVAL):
        raise ValueError(f"Batch '{batch_id}' is in status '{batch.status}' (must be APPROVED to apply).")

    recommendations = list(batch.recommendations.select_related('resource', 'request', 'assigned_volunteer').all())
    if not recommendations:
        raise ValueError(f"Batch '{batch_id}' contains no recommended allocations to commit.")

    committed_allocations = []
    created_tasks = []

    for rec in recommendations:
        # 1. Lock and re-validate resource
        resource = Resource.objects.select_for_update().filter(id=rec.resource_id).first()
        if not resource:
            raise ValueError(f"Stale plan error: Resource '{rec.resource_id}' no longer exists.")

        if resource.status != ResourceStatusChoices.AVAILABLE:
            raise ValueError(
                f"Stale plan conflict: Resource '{resource.name}' is no longer available (current status: {resource.status})."
            )

        if resource.available_quantity < rec.allocated_quantity:
            raise ValueError(
                f"Concurrent inventory conflict: Resource '{resource.name}' has {resource.available_quantity} available, "
                f"which is less than recommended {rec.allocated_quantity}."
            )

        # 2. Lock and re-validate request
        req = ResourceRequest.objects.select_for_update().filter(id=rec.request_id).first()
        if not req:
            raise ValueError(f"Stale plan error: Request '{rec.request_id}' no longer exists.")

        if req.remaining_quantity < rec.allocated_quantity:
            raise ValueError(
                f"Concurrent demand conflict: Request '{req.item_name}' only has {req.remaining_quantity} remaining, "
                f"cannot allocate {rec.allocated_quantity}."
            )

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
        )
        rec.created_allocation = alloc
        rec.status = RecommendationStatusChoices.APPLIED
        rec.save(update_fields=['created_allocation', 'status'])
        committed_allocations.append(alloc)

        # 6. Assign volunteer if designated
        volunteer = None
        if rec.assigned_volunteer_id:
            vol = Volunteer.objects.select_for_update().filter(id=rec.assigned_volunteer_id).first()
            if vol and vol.status == VolunteerAvailabilityChoices.AVAILABLE:
                volunteer = vol
                vol.status = VolunteerAvailabilityChoices.BUSY
                vol.save(update_fields=['status'])

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
            pickup_address=resource.provider.address,
            delivery_address=req.delivery_address or req.recipient.address,
            pickup_contact_phone=resource.provider.contact_phone,
            delivery_contact_phone=req.recipient.contact_phone,
            pickup_time_window=f"{resource.pickup_start.strftime('%H:%M')} - {resource.pickup_end.strftime('%H:%M')}",
            delivery_deadline=req.urgency_deadline,
            is_disaster_mode=resource.is_disaster_relief or req.is_disaster_relief,
            disaster_event=resource.disaster_event or req.disaster_event
        )
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
