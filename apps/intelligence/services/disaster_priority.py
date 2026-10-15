from typing import List, Dict, Any, Optional
from django.utils import timezone
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.resources.models import Resource, ResourceStatusChoices, ResourceCategoryChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices

CRITICAL_RELIEF_CATEGORIES = {
    ResourceCategoryChoices.DRINKING_WATER,
    ResourceCategoryChoices.COOKED_MEALS,
    ResourceCategoryChoices.MEDICAL_SUPPLIES,
    ResourceCategoryChoices.HYGIENE_KITS,
    ResourceCategoryChoices.BLANKETS_BEDDING,
}

def analyze_disaster_emergency_needs(
    disaster_event_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes active disaster relief requisitions, shortfall, and urgency hierarchy.
    Never overrides food safety or organization permissions.
    """
    now = timezone.now()

    disaster_qs = DisasterEvent.objects.filter(status=DisasterStatusChoices.ACTIVE)
    if disaster_event_id:
        disaster_qs = disaster_qs.filter(id=disaster_event_id)

    active_disaster = disaster_qs.first()
    if not active_disaster:
        return {
            'has_active_disaster': False,
            'message': 'No active disaster event declared.',
            'urgent_requests': [],
            'category_shortages': {},
            'unmatched_emergency_count': 0,
        }

    # Query open disaster relief requests
    open_emergency_reqs = ResourceRequest.objects.filter(
        disaster_event_id=active_disaster.id,
        status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED]
    ).select_related('recipient')

    # Available disaster relief or commercial surplus resources
    available_resources = Resource.objects.filter(
        status=ResourceStatusChoices.AVAILABLE,
        pickup_end__gt=now
    )

    supply_by_category: Dict[str, float] = {}
    for res in available_resources:
        cat = res.category
        supply_by_category[cat] = round(supply_by_category.get(cat, 0.0) + float(res.available_quantity), 2)

    demand_by_category: Dict[str, float] = {}
    urgent_ranked_requests = []

    for req in open_emergency_reqs:
        cat = req.category
        needed = float(req.remaining_quantity)
        demand_by_category[cat] = round(demand_by_category.get(cat, 0.0) + needed, 2)

        # Compute priority score
        score = 0
        if req.priority == RequestPriorityChoices.URGENT:
            score += 100
        elif req.priority == RequestPriorityChoices.HIGH:
            score += 60
        else:
            score += 30

        if cat in CRITICAL_RELIEF_CATEGORIES:
            score += 50

        # Urgent deadline proximity
        hours_to_deadline = max(0.1, (req.urgency_deadline - now).total_seconds() / 3600.0)
        if hours_to_deadline <= 4:
            score += 80
        elif hours_to_deadline <= 12:
            score += 40

        avail_for_cat = supply_by_category.get(cat, 0.0)
        is_covered = avail_for_cat >= needed

        urgent_ranked_requests.append({
            'request_id': req.id,
            'item_name': req.item_name,
            'category': cat,
            'recipient_name': req.recipient.name,
            'remaining_quantity': needed,
            'unit': req.unit,
            'priority': req.priority,
            'priority_score': score,
            'hours_to_deadline': round(hours_to_deadline, 1),
            'people_impacted': req.people_impacted,
            'is_fully_covered_by_current_supply': is_covered,
            'available_category_supply': avail_for_cat,
        })

    # Sort requests by priority score descending
    urgent_ranked_requests.sort(key=lambda r: r['priority_score'], reverse=True)

    # Compute category shortages
    category_shortages = {}
    all_cats = set(supply_by_category.keys()) | set(demand_by_category.keys())
    for cat in all_cats:
        dem = demand_by_category.get(cat, 0.0)
        sup = supply_by_category.get(cat, 0.0)
        shortage = max(0.0, dem - sup)
        if dem > 0:
            category_shortages[cat] = {
                'demand': dem,
                'available_supply': sup,
                'shortage': round(shortage, 2),
                'fulfillment_capability_pct': round((min(sup, dem) / dem * 100.0) if dem > 0 else 100.0, 1),
                'is_critical_life_support': cat in CRITICAL_RELIEF_CATEGORIES,
            }

    return {
        'has_active_disaster': True,
        'disaster_id': active_disaster.id,
        'disaster_title': active_disaster.title,
        'disaster_severity': active_disaster.severity,
        'affected_location': active_disaster.affected_location,
        'affected_population': active_disaster.affected_population,
        'open_emergency_requests_count': open_emergency_reqs.count(),
        'ranked_emergency_requests': urgent_ranked_requests,
        'category_shortages': category_shortages,
        'unmatched_emergency_count': len([r for r in urgent_ranked_requests if not r['is_fully_covered_by_current_supply']]),
    }
