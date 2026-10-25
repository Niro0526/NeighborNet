"""Automatic post-commit CP-SAT offers; offers never reserve stock."""
from django.db import transaction
from django.utils import timezone
from apps.intelligence.models import RecommendationBatch, OptimizationRecommendation, RecommendationStatusChoices, OperatingModeChoices, IntelligenceMethodChoices
from apps.intelligence.services.optimizer import solve_resource_allocation
from apps.intelligence.services.explainability import format_allocation_explanation
from apps.notifications.services import send_notification
from apps.requests.models import ResourceRequest, RequestStatusChoices

@transaction.atomic
def create_offers_for_resource(resource, created_by=None):
    if resource.status != 'AVAILABLE' or resource.pickup_end <= timezone.now(): return None
    OptimizationRecommendation.objects.select_for_update().filter(resource=resource, status=RecommendationStatusChoices.PENDING_APPROVAL, ngo_response='PENDING').update(status=RecommendationStatusChoices.SUPERSEDED)
    requests = list(ResourceRequest.objects.filter(is_disaster_relief=resource.is_disaster_relief, status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED], disaster_event_id=resource.disaster_event_id).select_related('recipient'))
    active_pairs = set(OptimizationRecommendation.objects.filter(resource=resource, status__in=[RecommendationStatusChoices.PENDING_APPROVAL, RecommendationStatusChoices.APPROVED]).values_list('resource_id', 'request_id'))
    plan = solve_resource_allocation([resource], requests, time_limit_seconds=5, now=timezone.now(), include_pickup=True, excluded_pairs=active_pairs)
    if not plan.allocations: return None
    batch = RecommendationBatch.objects.create(mode=OperatingModeChoices.DISASTER if resource.is_disaster_relief else OperatingModeChoices.NORMAL, method=IntelligenceMethodChoices.ORTOOLS_CPSAT, status=RecommendationStatusChoices.PENDING_APPROVAL, created_by=created_by, solver_status=plan.solver_status, runtime_ms=plan.runtime_ms, total_allocated_quantity=plan.total_allocated_quantity, fulfilled_demand_pct=plan.fulfilled_demand_pct, unmet_demand=plan.unmet_demand, solver_metadata={**plan.metadata, 'automatic': True, 'trigger': 'resource_publish_or_update'})
    requests_by_id = {r.pk: r for r in requests}
    for row in plan.allocations:
        req = requests_by_id[row['request_id']]
        name = row['volunteer_name'] or 'NGO pickup'
        exp = format_allocation_explanation(resource.name, req.recipient.name, row['allocated_quantity'], row['unit'], row['distance_km'], req.priority, batch.solver_status, row['constraints_satisfied'], name)
        rec = OptimizationRecommendation.objects.create(batch=batch, resource=resource, request=req, allocated_quantity=row['allocated_quantity'], unit=row['unit'], estimated_distance_km=row['distance_km'], distance_type=row['distance_type'], deadline_urgency=req.priority, explanation=exp['summary'], suggested_action=exp['suggested_action'], assigned_volunteer_id=row['assigned_volunteer_id'], logistics='VOLUNTEER' if row['assigned_volunteer_id'] else 'PICKUP_ONLY', volunteer_feasibility_notes=' '.join(row['missing_information']), constraints_satisfied=row['constraints_satisfied'], status=RecommendationStatusChoices.PENDING_APPROVAL)
        send_notification('New food match offer', f'{resource.name}: {rec.allocated_quantity} {rec.unit} available. Accept or decline before the pickup/safety deadline.', organization=req.recipient, action_url='/dashboard', event_key=f'match-offer-{rec.pk}')
    return batch

def schedule_matching(resource, user=None):
    transaction.on_commit(lambda: create_offers_for_resource(resource, user))
