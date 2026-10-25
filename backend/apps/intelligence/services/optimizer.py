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

def solve_resource_allocation(resources, requests, time_limit_seconds=10.0, now=None, include_pickup=False, excluded_pairs=None, excluded_volunteers=None):
    """Joint CP-SAT allocation and courier assignment, with exact per-unit conservation."""
    import math
    from .volunteer_assignment import volunteer_candidates
    start=time.perf_counter(); now=now or timezone.now()
    model=cp_model.CpModel(); variables={}; used={}; meta={}; rejected=[]
    def scaled(value): return math.floor((float(value)+1e-9)*SCALE_FACTOR)
    for resource in resources:
        for request in requests:
            if (resource.pk, request.pk) in (excluded_pairs or set()):
                continue
            eligibility=evaluate_resource_request_eligibility(resource,request,now)
            candidates,reasons=volunteer_candidates(resource,request,now) if eligibility.is_eligible else ([],eligibility.reasons_rejected)
            candidates = [c for c in candidates if c['volunteer'].pk not in (excluded_volunteers or set())]
            if include_pickup and eligibility.is_eligible:
                candidates.append(dict(volunteer=None, capacity=eligibility.compatible_quantity, missing_information=['NGO must arrange pickup before the safe-use deadline.']))
            if not candidates:
                rejected.append(dict(resource_id=resource.pk,request_id=request.pk,reasons=reasons,missing_information=eligibility.missing_information)); continue
            for candidate in candidates:
                volunteer=candidate['volunteer']
                limit=min(scaled(resource.available_quantity),scaled(request.remaining_quantity),scaled(candidate['capacity']))
                if resource.unit in ['meals','kits','items','packs','portions','bottles','boxes','packages']:
                    limit=(limit//100)*100
                if limit<=0: continue
                key=(resource.pk,request.pk,volunteer.pk if volunteer else 'PICKUP_'+resource.pk+'_'+request.pk)
                x=model.new_int_var(0,limit,'quantity_'+'_'.join(key))
                selected=model.new_bool_var('mission_'+'_'.join(key))
                model.add(x<=limit*selected); model.add(x>=selected)
                if resource.unit in ['meals','kits','items','packs','portions','bottles','boxes','packages']:
                    whole=model.new_int_var(0,limit//100,'whole_'+'_'.join(key)); model.add(x==whole*100)
                variables[key]=x; used[key]=selected
                meta[key]=(resource,request,eligibility,candidate)
    for resource in resources:
        model.add(sum(x for (rid,_,_),x in variables.items() if rid==resource.pk)<=scaled(resource.available_quantity))
    for request in requests:
        terms=[x for (_,qid,_),x in variables.items() if qid==request.pk]
        if request.allow_partial: model.add(sum(terms)<=scaled(request.remaining_quantity))
        else:
            full=model.new_bool_var('full_'+request.pk)
            model.add(sum(terms)==scaled(request.remaining_quantity)*full)
    # One courier has one mission, and a resource/request pair is a single task.
    for vid in {key[2] for key in variables}:
        model.add(sum(flag for key,flag in used.items() if key[2]==vid)<=1)
    for rid,qid in {(key[0],key[1]) for key in variables}:
        model.add(sum(flag for key,flag in used.items() if key[:2]==(rid,qid))<=1)
    terms=[]
    for key,x in variables.items():
        resource,request,eligibility,candidate=meta[key]
        priority={'urgent':1600,'high':1400,'medium':1200,'low':1000}.get(request.priority,1000)
        # Optimize fractions of demand, not a meaningless sum of kg, meals and liters.
        hours_left=(resource.safe_until-now).total_seconds()/3600 if resource.safe_until else float('inf')
        expiry_bonus=200 if hours_left<=6 else 100 if hours_left<=24 else 0
        coefficient=max(1,round((priority+expiry_bonus)*1000000/max(1,scaled(request.remaining_quantity)))-round(eligibility.distance_km*5))
        if candidate['volunteer']:
            coefficient += 1  # Prefer a feasible courier when quantities are otherwise equal.
        terms.append(x*coefficient)
    if terms: model.maximize(sum(terms))
    solver=cp_model.CpSolver(); solver.parameters.max_time_in_seconds=time_limit_seconds; solver.parameters.num_workers=4
    status=solver.solve(model)
    status_name={cp_model.OPTIMAL:'OPTIMAL',cp_model.FEASIBLE:'FEASIBLE',cp_model.INFEASIBLE:'INFEASIBLE',cp_model.MODEL_INVALID:'MODEL_INVALID',cp_model.UNKNOWN:'UNKNOWN'}[status]
    rows=[]; res_used={r.pk:0.0 for r in resources}; req_used={q.pk:0.0 for q in requests}
    if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
        for key,x in variables.items():
            value=solver.value(x)/100
            if value<=0: continue
            resource,request,eligibility,candidate=meta[key]
            res_used[resource.pk]+=value; req_used[request.pk]+=value
            rows.append(dict(resource_id=resource.pk,request_id=request.pk,resource_name=resource.name,request_item_name=request.item_name,provider_name=resource.provider.name,recipient_name=request.recipient.name,allocated_quantity=value,unit=resource.unit,distance_km=eligibility.distance_km,distance_type=eligibility.distance_type,assigned_volunteer_id=candidate['volunteer'].pk if candidate['volunteer'] else None,volunteer_name=candidate['volunteer'].full_name if candidate['volunteer'] else None,missing_information=candidate['missing_information'],constraints_satisfied=eligibility.constraints_satisfied,match_score=0,explanation='CP-SAT feasible recommendation. NGO acceptance and coordinator approval are required.'))
    units={r.unit for r in resources}|{q.unit for q in requests}
    by_unit={unit:dict(supply=round(sum(r.available_quantity for r in resources if r.unit==unit),2),demand=round(sum(q.remaining_quantity for q in requests if q.unit==unit),2),allocated=round(sum(row['allocated_quantity'] for row in rows if row['unit']==unit),2)) for unit in units}
    for data in by_unit.values():
        data['remaining_inventory']=round(data['supply']-data['allocated'],2); data['unmet_demand']=round(data['demand']-data['allocated'],2)
    allocated=sum(row['allocated_quantity'] for row in rows) if len(units)==1 else 0
    demand=sum(q.remaining_quantity for q in requests) if len(units)==1 else 0
    percent=100*sum(req_used[q.pk]/q.remaining_quantity for q in requests if q.remaining_quantity>0)/max(1,len([q for q in requests if q.remaining_quantity>0]))
    metadata=dict(num_resources=len(resources),num_requests=len(requests),num_candidate_pairs=len({key[:2] for key in variables}),num_courier_variables=len(variables),units=by_unit,rejected_pairs=rejected,remaining_inventory={r.pk:round(r.available_quantity-res_used[r.pk],2) for r in resources},remaining_demand={q.pk:round(q.remaining_quantity-req_used[q.pk],2) for q in requests},warnings=sorted({warning for row in rows for warning in row['missing_information']}),empty_reason='No feasible resource/request/courier combination in recorded data.' if not rows else None)
    return OptimizationPlanResult(status_name,rows,allocated,demand,percent,sum(v['unmet_demand'] for v in by_unit.values()) if len(units)==1 else 0,sum(v['remaining_inventory'] for v in by_unit.values()) if len(units)==1 else 0,sum(row['distance_km'] for row in rows)/len(rows) if rows else 0,(time.perf_counter()-start)*1000,solver.objective_value if status in [cp_model.OPTIMAL,cp_model.FEASIBLE] else 0,metadata)
