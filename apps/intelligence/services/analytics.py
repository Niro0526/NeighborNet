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
