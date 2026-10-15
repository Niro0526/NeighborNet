from typing import Dict, Any, Optional, List
from django.db import transaction
from django.utils import timezone
from apps.deliveries.models import (
    DeliveryTask, DeliveryTaskStatusChoices,
    Allocation, AllocationStatusChoices
)
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from apps.resources.models import Resource, ResourceStatusChoices
from apps.intelligence.models import (
    DisruptionEvent, DisruptionTypeChoices, DisruptionStatusChoices,
    RecommendationBatch, OptimizationRecommendation,
    RecommendationStatusChoices, OperatingModeChoices, IntelligenceMethodChoices
)
from .volunteer_assignment import match_volunteer_for_allocation
from .distance import calculate_haversine_distance

def create_disruption_and_preview_recovery(
    task_id: str,
    event_type: str,
    details: str,
    user=None
) -> Dict[str, Any]:
    """
    Records a delivery disruption and computes an explainable replacement plan for Coordinator review.
    Does not mutate completed deliveries or execute changes autonomously.
    """
    task = DeliveryTask.objects.select_related('allocation', 'resource', 'request', 'volunteer').filter(id=task_id).first()
    if not task:
        raise ValueError(f"Delivery Task '{task_id}' not found.")

    if task.status == DeliveryTaskStatusChoices.DELIVERED:
        raise ValueError("Cannot disrupt a task that is already DELIVERED.")

    original_plan_summary = {
        'task_id': task.id,
        'title': task.title,
        'status': task.status,
        'quantity': task.quantity,
        'unit': task.unit,
        'resource_id': task.resource_id,
        'request_id': task.request_id,
        'volunteer_id': task.volunteer_id,
        'volunteer_name': task.volunteer.full_name if task.volunteer else 'Unassigned',
        'pickup_address': task.pickup_address,
        'delivery_address': task.delivery_address,
    }

    # Record Disruption Event
    disruption = DisruptionEvent.objects.create(
        task=task,
        event_type=event_type,
        reported_by=user,
        details=details,
        affected_quantity=task.quantity,
        original_plan_summary=original_plan_summary,
        status=DisruptionStatusChoices.REPORTED,
    )

    # Transition task to DISRUPTED state
    task.status = DeliveryTaskStatusChoices.DISRUPTED
    task.disruption_reason = details
    task.save(update_fields=['status', 'disruption_reason'])

    # Compute Replacement Plan
    replacement_options: List[Dict[str, Any]] = []

    # Scenario 1: Courier cancellation / unavailability -> Reassign replacement courier
    if event_type in [
        DisruptionTypeChoices.VOLUNTEER_CANCEL,
        DisruptionTypeChoices.VOLUNTEER_UNAVAILABLE,
        DisruptionTypeChoices.ROAD_RESTRICTION,
        DisruptionTypeChoices.PICKUP_DELAY,
    ]:
        excluded_volunteers = set()
        if task.volunteer_id:
            excluded_volunteers.add(task.volunteer_id)

        alt_courier = match_volunteer_for_allocation(
            resource=task.resource,
            request=task.request,
            allocated_quantity=task.quantity,
            assigned_volunteer_ids=excluded_volunteers
        )

        if alt_courier.is_feasible and alt_courier.volunteer:
            replacement_options.append({
                'type': 'REASSIGN_VOLUNTEER',
                'description': f"Reassign task to available courier {alt_courier.volunteer.full_name} ({alt_courier.volunteer.get_vehicle_type_display()}).",
                'replacement_volunteer_id': alt_courier.volunteer.id,
                'replacement_volunteer_name': alt_courier.volunteer.full_name,
                'vehicle_capacity_kg': alt_courier.volunteer.vehicle_capacity_kg,
                'staging_distance_km': alt_courier.pickup_distance_km,
                'feasibility_notes': alt_courier.notes,
            })
        else:
            replacement_options.append({
                'type': 'NO_AVAILABLE_COURIER',
                'description': "No immediate replacement courier found with required vehicle capacity.",
                'feasibility_notes': alt_courier.notes,
            })

    # Scenario 2: Resource withdrawal or lot expiration -> Seek alternative donor lot
    if event_type in [DisruptionTypeChoices.RESOURCE_WITHDRAWAL, DisruptionTypeChoices.RESOURCE_EXPIRY]:
        now = timezone.now()
        alt_resources = Resource.objects.filter(
            category=task.resource.category,
            status=ResourceStatusChoices.AVAILABLE,
            pickup_end__gt=now
        ).exclude(id=task.resource_id)

        found_alt = False
        for alt_res in alt_resources:
            if alt_res.available_quantity >= task.quantity:
                dist = calculate_haversine_distance(
                    alt_res.provider.latitude, alt_res.provider.longitude,
                    task.request.recipient.latitude, task.request.recipient.longitude
                )
                replacement_options.append({
                    'type': 'SUBSTITUTE_RESOURCE',
                    'description': f"Substitute with available food lot '{alt_res.name}' from '{alt_res.provider.name}' ({alt_res.available_quantity} {alt_res.unit} available).",
                    'replacement_resource_id': alt_res.id,
                    'replacement_resource_name': alt_res.name,
                    'provider_name': alt_res.provider.name,
                    'distance_km': dist,
                })
                found_alt = True
                break

        if not found_alt:
            replacement_options.append({
                'type': 'INVENTORY_SHORTAGE',
                'description': "No alternative donor lot found with sufficient capacity.",
            })

    # Draft a replacement RecommendationBatch
    batch = RecommendationBatch.objects.create(
        mode=OperatingModeChoices.DISASTER if task.is_disaster_mode else OperatingModeChoices.NORMAL,
        method=IntelligenceMethodChoices.ORTOOLS_CPSAT,
        status=RecommendationStatusChoices.PENDING_APPROVAL,
        created_by=user,
        solver_status='FEASIBLE' if replacement_options else 'INFEASIBLE',
        total_allocated_quantity=task.quantity,
        notes=f"Recovery plan generated for Disruption Event #{disruption.id} on Task #{task.id}.",
        solver_metadata={'disruption_id': disruption.id, 'replacement_options': replacement_options}
    )

    disruption.replacement_batch = batch
    disruption.status = DisruptionStatusChoices.RECOVERY_PROPOSED
    disruption.save(update_fields=['replacement_batch', 'status'])

    return {
        'disruption_id': disruption.id,
        'task_id': task.id,
        'event_type': event_type,
        'original_plan': original_plan_summary,
        'replacement_options': replacement_options,
        'recovery_batch_id': batch.id,
        'approval_required': True,
    }

@transaction.atomic
def apply_recovery_plan(disruption_id: str, approved_by_user) -> Dict[str, Any]:
    """
    Applies an approved recovery plan atomically with row locking.
    """
    disruption = DisruptionEvent.objects.select_for_update().filter(id=disruption_id).first()
    if not disruption:
        raise ValueError(f"Disruption Event '{disruption_id}' not found.")

    if disruption.status == DisruptionStatusChoices.RESOLVED:
        raise ValueError("Disruption recovery has already been applied and resolved.")

    task = DeliveryTask.objects.select_for_update().filter(id=disruption.task_id).first()
    if not task:
        raise ValueError("Associated delivery task not found.")

    batch = disruption.replacement_batch
    options = batch.solver_metadata.get('replacement_options', []) if batch else []

    applied_action = None
    for opt in options:
        if opt.get('type') == 'REASSIGN_VOLUNTEER':
            vol_id = opt.get('replacement_volunteer_id')
            new_vol = Volunteer.objects.select_for_update().filter(id=vol_id).first()
            if new_vol:
                # Update task courier assignment
                task.volunteer = new_vol
                task.status = DeliveryTaskStatusChoices.AVAILABLE  # Reset to available/reassigned
                task.save(update_fields=['volunteer', 'status'])

                # Update new volunteer status
                new_vol.status = VolunteerAvailabilityChoices.BUSY
                new_vol.save(update_fields=['status'])

                applied_action = f"Task #{task.id} reassigned to courier {new_vol.full_name}."
                break

    disruption.status = DisruptionStatusChoices.RESOLVED
    disruption.resolution_notes = applied_action or "Recovery resolved by Coordinator."
    disruption.resolved_at = timezone.now()
    disruption.save(update_fields=['status', 'resolution_notes', 'resolved_at'])

    if batch:
        batch.status = RecommendationStatusChoices.APPLIED
        batch.approved_by = approved_by_user
        batch.approved_at = timezone.now()
        batch.applied_by = approved_by_user
        batch.applied_at = timezone.now()
        batch.save(update_fields=['status', 'approved_by', 'approved_at', 'applied_by', 'applied_at'])

    return {
        'success': True,
        'disruption_id': disruption.id,
        'resolution': applied_action or "Recovery plan successfully committed.",
        'task_status': task.status,
    }
