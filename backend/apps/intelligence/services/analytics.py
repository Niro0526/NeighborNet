import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, Any
from django.utils import timezone
from django.db.models import Sum, Count, Q

from apps.resources.models import Resource, ResourceStatusChoices
from apps.requests.models import ResourceRequest, RequestStatusChoices, RequestPriorityChoices
from apps.deliveries.models import DeliveryTask, DeliveryTaskStatusChoices, Allocation, AllocationStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices
from apps.intelligence.models import RecommendationBatch, DisruptionEvent

def compute_data_intelligence_analytics() -> Dict[str, Any]:
    """
    Computes rigorous descriptive analytics using Pandas and NumPy from live PostgreSQL records.
    Never fabricates metrics. Explicitly separates confirmed rescued food from pending allocations.
    """
    now = timezone.now()

    # 1. Resource Inventory DataFrame
    res_qs = Resource.objects.values(
        'id', 'category', 'quantity', 'allocated_quantity', 'status', 'safe_until', 'pickup_end'
    )
    df_res = pd.DataFrame(list(res_qs))

    if not df_res.empty:
        df_res['available_quantity'] = df_res['quantity'] - df_res['allocated_quantity']
        total_supply_kg = float(df_res['quantity'].sum())
        available_supply_kg = float(df_res['available_quantity'].sum())
        allocated_supply_kg = float(df_res['allocated_quantity'].sum())
        
        # Categorical distribution
        cat_supply = df_res.groupby('category')['available_quantity'].sum().to_dict()

        # Shelf-life vulnerability: lots expiring within 24 hours
        expiring_mask = (df_res['status'] == ResourceStatusChoices.AVAILABLE) & (
            pd.to_datetime(df_res['safe_until']) <= pd.to_datetime(now + timedelta(hours=24))
        )
        expiring_soon_kg = float(df_res[expiring_mask]['available_quantity'].sum()) if any(expiring_mask) else 0.0
    else:
        total_supply_kg = 0.0
        available_supply_kg = 0.0
        allocated_supply_kg = 0.0
        cat_supply = {}
        expiring_soon_kg = 0.0

    # 2. Requisition Demand DataFrame
    req_qs = ResourceRequest.objects.values(
        'id', 'category', 'requested_quantity', 'fulfilled_quantity',
        'priority', 'status', 'is_disaster_relief', 'people_impacted'
    )
    df_req = pd.DataFrame(list(req_qs))

    if not df_req.empty:
        df_req['remaining_quantity'] = df_req['requested_quantity'] - df_req['fulfilled_quantity']
        total_demand_kg = float(df_req['requested_quantity'].sum())
        fulfilled_demand_kg = float(df_req['fulfilled_quantity'].sum())
        unmet_demand_kg = float(df_req['remaining_quantity'].sum())
        total_people_impacted = int(df_req['people_impacted'].sum())

        cat_demand = df_req.groupby('category')['remaining_quantity'].sum().to_dict()
        priority_breakdown = df_req.groupby('priority')['remaining_quantity'].sum().to_dict()
    else:
        total_demand_kg = 0.0
        fulfilled_demand_kg = 0.0
        unmet_demand_kg = 0.0
        total_people_impacted = 0
        cat_demand = {}
        priority_breakdown = {}

    # 3. Delivery Execution & Realized Food Rescue
    # Strictly label food as RESCUED only upon DELIVERED confirmation
    task_qs = DeliveryTask.objects.values('id', 'quantity', 'status', 'is_disaster_mode')
    df_tasks = pd.DataFrame(list(task_qs))

    if not df_tasks.empty:
        delivered_mask = df_tasks['status'] == DeliveryTaskStatusChoices.DELIVERED
        active_in_transit_mask = df_tasks['status'].isin([
            DeliveryTaskStatusChoices.ACCEPTED,
            DeliveryTaskStatusChoices.ARRIVED_PICKUP,
            DeliveryTaskStatusChoices.PICKED_UP,
            DeliveryTaskStatusChoices.ARRIVED_DELIVERY
        ])
        disrupted_mask = df_tasks['status'] == DeliveryTaskStatusChoices.DISRUPTED

        confirmed_rescued_kg = float(df_tasks[delivered_mask]['quantity'].sum()) if any(delivered_mask) else 0.0
        active_delivery_kg = float(df_tasks[active_in_transit_mask]['quantity'].sum()) if any(active_in_transit_mask) else 0.0
        disrupted_tasks_count = int(disrupted_mask.sum())
        total_completed_tasks = int(delivered_mask.sum())
    else:
        confirmed_rescued_kg = 0.0
        active_delivery_kg = 0.0
        disrupted_tasks_count = 0
        total_completed_tasks = 0

    # 4. Volunteer Readiness
    vol_counts = Volunteer.objects.aggregate(
        total=Count('id'),
        available=Count('id', filter=Q(status=VolunteerAvailabilityChoices.AVAILABLE, verified=True)),
        busy=Count('id', filter=Q(status=VolunteerAvailabilityChoices.BUSY)),
        offline=Count('id', filter=Q(status=VolunteerAvailabilityChoices.OFFLINE)),
    )

    # 5. Optimization & Recommendation Pipeline Stats
    batch_stats = RecommendationBatch.objects.aggregate(
        total_batches=Count('id'),
        pending_approval=Count('id', filter=Q(status='PENDING_APPROVAL')),
        applied_batches=Count('id', filter=Q(status='APPLIED')),
    )

    # 6. Disaster Mode Sector Metrics
    active_disaster = DisasterEvent.objects.filter(status=DisasterStatusChoices.ACTIVE).first()
    disaster_metrics = None
    if active_disaster:
        em_qs = ResourceRequest.objects.filter(
            disaster_event_id=active_disaster.id,
            status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED]
        )
        em_open_count = em_qs.count()
        em_needed = float(em_qs.aggregate(total=Sum('requested_quantity'))['total'] or 0.0)
        em_fulfilled = float(em_qs.aggregate(total=Sum('fulfilled_quantity'))['total'] or 0.0)
        em_unmet = max(0.0, em_needed - em_fulfilled)

        disaster_metrics = {
            'disaster_id': active_disaster.id,
            'title': active_disaster.title,
            'severity': active_disaster.severity,
            'affected_location': active_disaster.affected_location,
            'affected_population': active_disaster.affected_population,
            'open_emergency_requests': em_open_count,
            'emergency_needed_kg': round(em_needed, 2),
            'emergency_unmet_kg': round(em_unmet, 2),
        }

    return {
        'timestamp': now.isoformat(),
        'inventory_metrics': {
            'total_registered_supply_kg': round(total_supply_kg, 2),
            'available_surplus_kg': round(available_supply_kg, 2),
            'allocated_supply_kg': round(allocated_supply_kg, 2),
            'expiring_within_24h_kg': round(expiring_soon_kg, 2),
            'supply_by_category': cat_supply,
        },
        'demand_metrics': {
            'total_demand_kg': round(total_demand_kg, 2),
            'fulfilled_demand_kg': round(fulfilled_demand_kg, 2),
            'unmet_demand_kg': round(unmet_demand_kg, 2),
            'overall_fulfillment_rate_pct': round((fulfilled_demand_kg / total_demand_kg * 100.0) if total_demand_kg > 0 else 0.0, 1),
            'total_people_impacted': total_people_impacted,
            'demand_by_category': cat_demand,
            'demand_by_priority': priority_breakdown,
        },
        'logistics_and_rescue_metrics': {
            'confirmed_rescued_kg': round(confirmed_rescued_kg, 2),
            'active_in_transit_kg': round(active_delivery_kg, 2),
            'completed_deliveries_count': total_completed_tasks,
            'reported_disruptions_count': disrupted_tasks_count,
        },
        'volunteer_fleet': {
            'total_volunteers': vol_counts['total'],
            'available_couriers': vol_counts['available'],
            'busy_on_delivery': vol_counts['busy'],
            'offline': vol_counts['offline'],
        },
        'optimizer_pipeline': {
            'total_batches': batch_stats['total_batches'],
            'pending_approval': batch_stats.get('pending_approval', 0),
            'applied_batches': batch_stats.get('applied_batches', 0),
        },
        'disaster_context': disaster_metrics,
    }


def compute_verified_impact_analytics() -> Dict[str, Any]:
    """
    Computes verified impact analytics following Part 6 strict rules:
    - Never mix kilograms, liters and discrete kits into a single quantity.
    - Explicit denominators for all percentages.
    - Separates allocated from delivered quantities.
    - Uses timestamps actually recorded in DB for transit duration.
    - Labels data provenance clearly.
    """
    now = timezone.now()
    from apps.organizations.models import Organization
    from apps.audit.models import ActivityLog

    # --- NORMAL COMMUNITY METRICS BY UNIT ---
    # 1. Total listed food grouped by unit
    listed_by_unit_qs = Resource.objects.values('unit').annotate(total_quantity=Sum('quantity'))
    total_food_listed = {row['unit']: round(float(row['total_quantity']), 2) for row in listed_by_unit_qs}

    # 2. Eligible food listed (safe_until in future or null, status AVAILABLE or RESERVED)
    eligible_qs = Resource.objects.filter(
        Q(safe_until__gt=now) | Q(safe_until__isnull=True),
        status__in=[ResourceStatusChoices.AVAILABLE, ResourceStatusChoices.RESERVED]
    ).values('unit').annotate(total_quantity=Sum('quantity'))
    eligible_food_listed = {row['unit']: round(float(row['total_quantity']), 2) for row in eligible_qs}

    # 3. Total allocated quantity by unit
    allocated_qs = Allocation.objects.values('resource__unit').annotate(total_alloc=Sum('allocated_quantity'))
    total_allocated_by_unit = {row['resource__unit']: round(float(row['total_alloc']), 2) for row in allocated_qs}

    # 4. Total delivered quantity by unit (from DELIVERED tasks only)
    delivered_qs = DeliveryTask.objects.filter(
        status=DeliveryTaskStatusChoices.DELIVERED
    ).values('unit').annotate(total_delivered=Sum('quantity'))
    total_delivered_by_unit = {row['unit']: round(float(row['total_delivered']), 2) for row in delivered_qs}

    # 5. Delivery counts and transit duration calculation
    completed_deliveries = DeliveryTask.objects.filter(status=DeliveryTaskStatusChoices.DELIVERED)
    completed_deliveries_count = completed_deliveries.count()

    # Calculate average pickup-to-delivery time ONLY from tasks where both timestamps were recorded in DB
    valid_timing_tasks = completed_deliveries.filter(
        picked_up_at__isnull=False,
        delivered_at__isnull=False
    )
    if valid_timing_tasks.exists():
        durations = []
        for task in valid_timing_tasks:
            duration_minutes = (task.delivered_at - task.picked_up_at).total_seconds() / 60.0
            if duration_minutes >= 0:
                durations.append(duration_minutes)
        avg_pickup_to_delivery_min = round(float(np.mean(durations)), 1) if durations else None
    else:
        avg_pickup_to_delivery_min = None

    # 6. Organization participation
    verified_orgs_count = Organization.objects.filter(verified=True).count()
    total_orgs_count = Organization.objects.count()

    # 7. Requisition demand & fulfillment rate with EXPLICIT DENOMINATORS
    demand_by_unit_qs = ResourceRequest.objects.values('unit').annotate(
        total_requested=Sum('requested_quantity'),
        total_fulfilled=Sum('fulfilled_quantity')
    )
    fulfillment_by_unit = {}
    unmet_demand_by_unit = {}
    for row in demand_by_unit_qs:
        unit = row['unit']
        req_qty = float(row['total_requested'] or 0.0)
        ful_qty = float(row['total_fulfilled'] or 0.0)
        unmet_demand_by_unit[unit] = round(max(0.0, req_qty - ful_qty), 2)
        fulfillment_by_unit[unit] = {
            'allocated': round(ful_qty, 2),
            'requested': round(req_qty, 2),
            'denominator': round(req_qty, 2),
            'fulfillmentPercentage': round((ful_qty / req_qty * 100.0) if req_qty > 0 else 0.0, 1),
        }

    # 8. Expired or withdrawn quantity by unit
    expired_withdrawn_qs = Resource.objects.filter(
        status__in=[ResourceStatusChoices.EXPIRED, ResourceStatusChoices.WITHDRAWN]
    ).values('unit').annotate(total_loss=Sum('quantity'))
    expired_withdrawn_by_unit = {row['unit']: round(float(row['total_loss']), 2) for row in expired_withdrawn_qs}

    # --- DISASTER METRICS ---
    disaster_reqs = ResourceRequest.objects.filter(is_disaster_relief=True)
    disaster_requests_received = disaster_reqs.count()
    disaster_requests_fulfilled = disaster_reqs.filter(status=RequestStatusChoices.FULFILLED).count()
    disaster_requests_partially_fulfilled = disaster_reqs.filter(status=RequestStatusChoices.PARTIALLY_ALLOCATED).count()
    pending_urgent_requests = disaster_reqs.filter(
        status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED],
        priority=RequestPriorityChoices.URGENT
    ).count()

    # Disaster quantities allocated strictly grouped by unit
    disaster_alloc_qs = Allocation.objects.filter(
        request__is_disaster_relief=True
    ).values('resource__unit').annotate(total_alloc=Sum('allocated_quantity'))
    disaster_alloc_by_unit = {row['resource__unit']: round(float(row['total_alloc']), 2) for row in disaster_alloc_qs}

    disaster_deliveries_completed = DeliveryTask.objects.filter(
        is_disaster_mode=True,
        status=DeliveryTaskStatusChoices.DELIVERED
    ).count()

    disruptions_recorded = DeliveryTask.objects.filter(
        status=DeliveryTaskStatusChoices.DISRUPTED
    ).count()

    recovery_plans_applied = ActivityLog.objects.filter(
        category='DISASTER',
        action__icontains='RECOVERY'
    ).count()

    # Provenance detection: Check if demo records exist
    is_demo = Resource.objects.filter(name__icontains='[DEMO]').exists() or Organization.objects.filter(name__icontains='[DEMO]').exists()

    return {
        'timestamp': now.isoformat(),
        'normal_community_metrics': {
            'total_food_listed_by_unit': total_food_listed,
            'eligible_food_listed_by_unit': eligible_food_listed,
            'total_quantity_allocated_by_unit': total_allocated_by_unit,
            'total_delivered_by_unit': total_delivered_by_unit,
            'completed_deliveries_count': completed_deliveries_count,
            'participating_verified_organizations_count': verified_orgs_count,
            'participating_total_organizations_count': total_orgs_count,
            'average_pickup_to_delivery_minutes': avg_pickup_to_delivery_min,
            'fulfillment_percentages_by_unit': fulfillment_by_unit,
            'unmet_demand_by_unit': unmet_demand_by_unit,
            'expired_or_withdrawn_by_unit': expired_withdrawn_by_unit,
        },
        'disaster_metrics': {
            'requests_received': disaster_requests_received,
            'requests_fulfilled': disaster_requests_fulfilled,
            'requests_partially_fulfilled': disaster_requests_partially_fulfilled,
            'pending_urgent_requests': pending_urgent_requests,
            'quantities_allocated_by_unit': disaster_alloc_by_unit,
            'deliveries_completed': disaster_deliveries_completed,
            'disruptions_recorded': disruptions_recorded,
            'recovery_plans_applied': recovery_plans_applied,
        },
        'data_provenance': {
            'is_synthetic_or_demo_data': is_demo,
            'dataSourceLabel': 'PostgreSQL Operational Database (Verified Records)',
            'methodology_disclaimer': 'Data directly aggregates committed PostgreSQL transactions. Carbon offsets and meal portions require formal field calibration and are not presented as certified credits.',
        }
    }

