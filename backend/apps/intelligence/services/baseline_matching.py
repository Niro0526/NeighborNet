import time
from typing import List, Dict, Any, Optional
from django.utils import timezone
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from .eligibility import evaluate_resource_request_eligibility
from .distance import calculate_haversine_distance

class BaselineMatchItem:
    def __init__(
        self,
        resource_id: str,
        request_id: str,
        resource_name: str,
        request_item_name: str,
        provider_name: str,
        recipient_name: str,
        allocated_quantity: float,
        unit: str,
        distance_km: float,
        explanation: str,
        constraints_satisfied: List[str],
    ):
        self.resource_id = resource_id
        self.request_id = request_id
        self.resource_name = resource_name
        self.request_item_name = request_item_name
        self.provider_name = provider_name
        self.recipient_name = recipient_name
        self.allocated_quantity = allocated_quantity
        self.unit = unit
        self.distance_km = distance_km
        self.explanation = explanation
        self.constraints_satisfied = constraints_satisfied

    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'request_id': self.request_id,
            'resource_name': self.resource_name,
            'request_item_name': self.request_item_name,
            'provider_name': self.provider_name,
            'recipient_name': self.recipient_name,
            'allocated_quantity': self.allocated_quantity,
            'unit': self.unit,
            'distance_km': self.distance_km,
            'explanation': self.explanation,
            'constraints_satisfied': self.constraints_satisfied,
        }

class BaselineOutput:
    def __init__(
        self,
        method: str,
        allocations: List[BaselineMatchItem],
        total_allocated_quantity: float,
        total_initial_demand: float,
        fulfilled_demand_pct: float,
        unmet_demand: float,
        leftover_inventory: float,
        avg_distance_km: float,
        runtime_ms: float,
    ):
        self.method = method
        self.allocations = allocations
        self.total_allocated_quantity = total_allocated_quantity
        self.total_initial_demand = total_initial_demand
        self.fulfilled_demand_pct = fulfilled_demand_pct
        self.unmet_demand = unmet_demand
        self.leftover_inventory = leftover_inventory
        self.avg_distance_km = avg_distance_km
        self.runtime_ms = runtime_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            'method': self.method,
            'allocations': [a.to_dict() for a in self.allocations],
            'total_allocated_quantity': round(self.total_allocated_quantity, 2),
            'total_initial_demand': round(self.total_initial_demand, 2),
            'fulfilled_demand_pct': round(self.fulfilled_demand_pct, 2),
            'unmet_demand': round(self.unmet_demand, 2),
            'leftover_inventory': round(self.leftover_inventory, 2),
            'avg_distance_km': round(self.avg_distance_km, 2),
            'runtime_ms': round(self.runtime_ms, 2),
        }

def run_fcfs_baseline(
    resources: List[Resource],
    requests: List[ResourceRequest],
    now=None
) -> BaselineOutput:
    """
    Baseline A: First-Come-First-Served (FCFS)
    Allocates eligible resources chronologically by creation timestamp.
    """
    start_t = time.perf_counter()
    if now is None:
        now = timezone.now()

    # Track mutable balances during simulation run without modifying database records
    avail_map = {r.id: float(r.available_quantity) for r in resources}
    demand_map = {req.id: float(req.remaining_quantity) for req in requests}
    total_initial_demand = sum(demand_map.values())

    # Sort requests chronologically (earliest request first)
    sorted_requests = sorted(requests, key=lambda req: getattr(req, 'created_at', None) or now)
    # Sort resources chronologically (earliest listed lot first)
    sorted_resources = sorted(resources, key=lambda r: getattr(r, 'created_at', None) or now)

    allocations: List[BaselineMatchItem] = []

    for req in sorted_requests:
        needed = demand_map[req.id]
        if needed <= 0:
            continue

        for res in sorted_resources:
            current_avail = avail_map[res.id]
            if current_avail <= 0:
                continue

            # Evaluate hard constraints
            elig = evaluate_resource_request_eligibility(res, req, now=now)
            if not elig.is_eligible:
                continue

            # Compute feasible allocation quantity
            alloc_qty = min(current_avail, needed)
            if alloc_qty <= 0:
                continue

            avail_map[res.id] -= alloc_qty
            demand_map[req.id] -= alloc_qty
            needed -= alloc_qty

            expl = (
                f"FCFS Rule: Allocated {alloc_qty} {res.unit} of '{res.name}' to '{req.recipient.name}' "
                f"based on chronological priority (Request #{req.id})."
            )

            allocations.append(BaselineMatchItem(
                resource_id=res.id,
                request_id=req.id,
                resource_name=res.name,
                request_item_name=req.item_name,
                provider_name=res.provider.name,
                recipient_name=req.recipient.name,
                allocated_quantity=round(alloc_qty, 2),
                unit=res.unit,
                distance_km=elig.distance_km,
                explanation=expl,
                constraints_satisfied=elig.constraints_satisfied,
            ))

            if needed <= 0:
                break

    end_t = time.perf_counter()
    runtime_ms = (end_t - start_t) * 1000.0

    total_allocated = sum(a.allocated_quantity for a in allocations)
    unmet_demand = sum(demand_map.values())
    leftover = sum(avail_map.values())
    fulfilled_pct = (total_allocated / total_initial_demand * 100.0) if total_initial_demand > 0 else 0.0
    avg_dist = (sum(a.distance_km for a in allocations) / len(allocations)) if allocations else 0.0

    return BaselineOutput(
        method='BASELINE_FCFS',
        allocations=allocations,
        total_allocated_quantity=total_allocated,
        total_initial_demand=total_initial_demand,
        fulfilled_demand_pct=fulfilled_pct,
        unmet_demand=unmet_demand,
        leftover_inventory=leftover,
        avg_distance_km=avg_dist,
        runtime_ms=runtime_ms,
    )

def run_nearest_baseline(
    resources: List[Resource],
    requests: List[ResourceRequest],
    now=None
) -> BaselineOutput:
    """
    Baseline B: Nearest Compatible Match
    Greedily allocates to eligible pairs with minimum straight-line geographic distance.
    """
    start_t = time.perf_counter()
    if now is None:
        now = timezone.now()

    avail_map = {r.id: float(r.available_quantity) for r in resources}
    demand_map = {req.id: float(req.remaining_quantity) for req in requests}
    total_initial_demand = sum(demand_map.values())

    # Build and sort all compatible candidate pairs by distance ascending
    candidate_pairs = []
    for req in requests:
        for res in resources:
            elig = evaluate_resource_request_eligibility(res, req, now=now)
            if elig.is_eligible:
                candidate_pairs.append({
                    'resource': res,
                    'request': req,
                    'distance_km': elig.distance_km,
                    'constraints': elig.constraints_satisfied,
                })

    # Sort pairs by distance (closest first)
    candidate_pairs.sort(key=lambda p: p['distance_km'])

    allocations: List[BaselineMatchItem] = []

    for pair in candidate_pairs:
        res = pair['resource']
        req = pair['request']

        current_avail = avail_map[res.id]
        needed = demand_map[req.id]

        if current_avail <= 0 or needed <= 0:
            continue

        alloc_qty = min(current_avail, needed)
        if alloc_qty <= 0:
            continue

        avail_map[res.id] -= alloc_qty
        demand_map[req.id] -= alloc_qty

        expl = (
            f"Nearest Compatible Rule: Allocated {alloc_qty} {res.unit} of '{res.name}' to '{req.recipient.name}' "
            f"based on minimal geographic distance ({pair['distance_km']} km)."
        )

        allocations.append(BaselineMatchItem(
            resource_id=res.id,
            request_id=req.id,
            resource_name=res.name,
            request_item_name=req.item_name,
            provider_name=res.provider.name,
            recipient_name=req.recipient.name,
            allocated_quantity=round(alloc_qty, 2),
            unit=res.unit,
            distance_km=pair['distance_km'],
            explanation=expl,
            constraints_satisfied=pair['constraints'],
        ))

    end_t = time.perf_counter()
    runtime_ms = (end_t - start_t) * 1000.0

    total_allocated = sum(a.allocated_quantity for a in allocations)
    unmet_demand = sum(demand_map.values())
    leftover = sum(avail_map.values())
    fulfilled_pct = (total_allocated / total_initial_demand * 100.0) if total_initial_demand > 0 else 0.0
    avg_dist = (sum(a.distance_km for a in allocations) / len(allocations)) if allocations else 0.0

    return BaselineOutput(
        method='BASELINE_NEAREST',
        allocations=allocations,
        total_allocated_quantity=total_allocated,
        total_initial_demand=total_initial_demand,
        fulfilled_demand_pct=fulfilled_pct,
        unmet_demand=unmet_demand,
        leftover_inventory=leftover,
        avg_distance_km=avg_dist,
        runtime_ms=runtime_ms,
    )
