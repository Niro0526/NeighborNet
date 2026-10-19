import time
from datetime import timedelta
from typing import List, Dict, Any, Optional, Tuple
from django.utils import timezone
from ortools.sat.python import cp_model

from apps.resources.models import Resource
from apps.requests.models import ResourceRequest, RequestPriorityChoices
from .eligibility import evaluate_resource_request_eligibility, EligibilityResult

SCALE_FACTOR = 100  # Scale continuous quantities (kg/liters) by 100 to allow exact integer arithmetic

class OptimizationPlanResult:
    def __init__(
        self,
        solver_status: str,
        allocations: List[Dict[str, Any]],
        total_allocated_quantity: float,
        total_initial_demand: float,
        fulfilled_demand_pct: float,
        unmet_demand: float,
        leftover_inventory: float,
        avg_distance_km: float,
        runtime_ms: float,
        objective_value: float,
        metadata: Dict[str, Any],
    ):
        self.solver_status = solver_status
        self.allocations = allocations
        self.total_allocated_quantity = total_allocated_quantity
        self.total_initial_demand = total_initial_demand
        self.fulfilled_demand_pct = fulfilled_demand_pct
        self.unmet_demand = unmet_demand
        self.leftover_inventory = leftover_inventory
        self.avg_distance_km = avg_distance_km
        self.runtime_ms = runtime_ms
        self.objective_value = objective_value
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            'solver_status': self.solver_status,
            'allocations': self.allocations,
            'total_allocated_quantity': round(self.total_allocated_quantity, 2),
            'total_initial_demand': round(self.total_initial_demand, 2),
            'fulfilled_demand_pct': round(self.fulfilled_demand_pct, 2),
            'unmet_demand': round(self.unmet_demand, 2),
            'leftover_inventory': round(self.leftover_inventory, 2),
            'avg_distance_km': round(self.avg_distance_km, 2),
            'runtime_ms': round(self.runtime_ms, 2),
            'objective_value': round(self.objective_value, 2),
            'metadata': self.metadata,
        }

def solve_resource_allocation(
    resources: List[Resource],
    requests: List[ResourceRequest],
    time_limit_seconds: float = 10.0,
    now=None
) -> OptimizationPlanResult:
    """
    Optimizes multi-criteria community resource allocation using Google OR-Tools CP-SAT solver.
    
    Decision Variables:
      X[i, j] in [0, min(avail_i, demand_j) * SCALE_FACTOR]
      Representing continuous quantity scaled by 100.
    
    Hard Constraints:
      1. Supply: sum_j X[i, j] <= avail_i * SCALE_FACTOR
      2. Demand: sum_i X[i, j] <= demand_j * SCALE_FACTOR
      3. Eligibility: X[i, j] == 0 if pair (i, j) fails any food safety/time/zone constraint.
    
    Multi-Criteria Objective:
      Maximize:
        + 1000 * sum(X[i, j]) [Fulfilled demand]
        + Priority weights * X[i, j] [Urgent & Disaster demand priority]
        + Expiry urgency * X[i, j] [Perishable surplus rescue]
        - Distance penalty * X[i, j] [Logistics travel burden reduction]
    """
    start_t = time.perf_counter()
    if now is None:
        now = timezone.now()

    model = cp_model.CpModel()

    total_initial_demand = sum(float(req.remaining_quantity) for req in requests)
    total_initial_supply = sum(float(res.available_quantity) for res in resources)

    # Pre-screen eligibility and create decision variables
    x_vars: Dict[Tuple[str, str], cp_model.IntVar] = {}
    pair_meta: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for res in resources:
        avail_scaled = int(round(float(res.available_quantity) * SCALE_FACTOR))
        if avail_scaled <= 0:
            continue

        for req in requests:
            demand_scaled = int(round(float(req.remaining_quantity) * SCALE_FACTOR))
            if demand_scaled <= 0:
                continue

            # Deterministic hard constraint screening
            elig: EligibilityResult = evaluate_resource_request_eligibility(res, req, now=now)
            if not elig.is_eligible:
                continue

            upper_bound = min(avail_scaled, demand_scaled)
            var_name = f"alloc_{res.id}_{req.id}"
            var = model.new_int_var(0, upper_bound, var_name)
            x_vars[(res.id, req.id)] = var

            pair_meta[(res.id, req.id)] = {
                'resource': res,
                'request': req,
                'distance_km': elig.distance_km,
                'constraints': elig.constraints_satisfied,
            }

    # Constraint 1: Resource Supply Limit
    for res in resources:
        res_vars = [x_vars[(res.id, req.id)] for req in requests if (res.id, req.id) in x_vars]
        if res_vars:
            max_supply_scaled = int(round(float(res.available_quantity) * SCALE_FACTOR))
            model.add(sum(res_vars) <= max_supply_scaled)

    # Constraint 2: Request Demand Limit
    for req in requests:
        req_vars = [x_vars[(res.id, req.id)] for res in resources if (res.id, req.id) in x_vars]
        if req_vars:
            max_demand_scaled = int(round(float(req.remaining_quantity) * SCALE_FACTOR))
            model.add(sum(req_vars) <= max_demand_scaled)

    # Build Multi-Criteria Objective Function
    objective_terms = []

    for (res_id, req_id), var in x_vars.items():
        meta = pair_meta[(res_id, req_id)]
        res = meta['resource']
        req = meta['request']
        dist_km = meta['distance_km']

        # 1. Base demand fulfillment reward
        coeff = 1000

        # 2. Priority & Disaster coverage reward
        if req.priority == RequestPriorityChoices.URGENT:
            coeff += 500
        elif req.priority == RequestPriorityChoices.HIGH:
            coeff += 300
        elif req.priority == RequestPriorityChoices.MEDIUM:
            coeff += 100

        if req.is_disaster_relief:
            coeff += 400

        # 3. Expiry risk bonus (prioritize food with short remaining shelf life)
        if res.safe_until:
            hours_left = (res.safe_until - now).total_seconds() / 3600.0
            if hours_left <= 6:
                coeff += 400
            elif hours_left <= 18:
                coeff += 250
            elif hours_left <= 36:
                coeff += 100

        # 4. Travel burden penalty (-5 per km)
        distance_penalty = int(round(dist_km * 5))
        coeff -= distance_penalty

        objective_terms.append(var * coeff)

    if objective_terms:
        model.maximize(sum(objective_terms))

    # Solver Configuration
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_workers = 4

    status_code = solver.solve(model)
    end_t = time.perf_counter()
    runtime_ms = (end_t - start_t) * 1000.0

    solver_status_str = {
        cp_model.OPTIMAL: 'OPTIMAL',
        cp_model.FEASIBLE: 'FEASIBLE',
        cp_model.INFEASIBLE: 'INFEASIBLE',
        cp_model.MODEL_INVALID: 'MODEL_INVALID',
        cp_model.UNKNOWN: 'UNKNOWN',
    }.get(status_code, 'UNKNOWN')

    allocations_output: List[Dict[str, Any]] = []
    total_allocated_qty = 0.0
    res_allocated_sums: Dict[str, float] = {r.id: 0.0 for r in resources}
    req_allocated_sums: Dict[str, float] = {req.id: 0.0 for req in requests}

    if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for (res_id, req_id), var in x_vars.items():
            scaled_val = solver.value(var)
            if scaled_val > 0:
                qty = round(scaled_val / float(SCALE_FACTOR), 2)
                meta = pair_meta[(res_id, req_id)]
                res = meta['resource']
                req = meta['request']
                dist_km = meta['distance_km']

                total_allocated_qty += qty
                res_allocated_sums[res_id] += qty
                req_allocated_sums[req_id] += qty

                expl = (
                    f"OR-Tools CP-SAT: Allocated {qty} {res.unit} of '{res.name}' to '{req.recipient.name}'. "
                    f"Optimized for demand fulfillment, priority ({req.priority.upper()}), "
                    f"shelf-life safety, and proximity ({dist_km} km)."
                )

                allocations_output.append({
                    'resource_id': res.id,
                    'request_id': req.id,
                    'resource_name': res.name,
                    'request_item_name': req.item_name,
                    'provider_name': res.provider.name,
                    'recipient_name': req.recipient.name,
                    'allocated_quantity': qty,
                    'unit': res.unit,
                    'distance_km': dist_km,
                    'match_score': 98.0 if solver_status_str == 'OPTIMAL' else 92.0,
                    'explanation': expl,
                    'constraints_satisfied': meta['constraints'],
                })

    leftover = sum(float(r.available_quantity) - res_allocated_sums[r.id] for r in resources)
    unmet = sum(float(req.remaining_quantity) - req_allocated_sums[req.id] for req in requests)
    fulfilled_pct = (total_allocated_qty / total_initial_demand * 100.0) if total_initial_demand > 0 else 0.0
    avg_dist = (sum(a['distance_km'] for a in allocations_output) / len(allocations_output)) if allocations_output else 0.0

    metadata = {
        'num_resources': len(resources),
        'num_requests': len(requests),
        'num_candidate_pairs': len(x_vars),
        'scale_factor': SCALE_FACTOR,
        'wall_time_s': solver.wall_time,
        'user_time_s': solver.user_time,
        'deterministic_time': solver.deterministic_time,
    }

    return OptimizationPlanResult(
        solver_status=solver_status_str,
        allocations=allocations_output,
        total_allocated_quantity=round(total_allocated_qty, 2),
        total_initial_demand=round(total_initial_demand, 2),
        fulfilled_demand_pct=round(fulfilled_pct, 2),
        unmet_demand=round(unmet, 2),
        leftover_inventory=round(leftover, 2),
        avg_distance_km=round(avg_dist, 2),
        runtime_ms=round(runtime_ms, 2),
        objective_value=round(solver.objective_value if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0.0, 2),
        metadata=metadata,
    )
