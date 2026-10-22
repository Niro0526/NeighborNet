"""Delivery feasibility from verified available courier records; no unit or travel guesses."""
import math
from datetime import timedelta
from django.utils import timezone
from apps.volunteers.models import Volunteer
from .distance import resource_coordinates, recorded_distance, MAX_SERVICE_RADIUS_KM
from .eligibility import evaluate_resource_request_eligibility, receiving_intervals

class VolunteerAssignmentResult:
    def __init__(self, volunteer, is_feasible, notes, pickup_distance_km=0.0):
        self.volunteer=volunteer; self.is_feasible=is_feasible; self.notes=notes; self.pickup_distance_km=pickup_distance_km
    def to_dict(self):
        return dict(volunteer_id=self.volunteer.pk if self.volunteer else None, volunteer_name=self.volunteer.full_name if self.volunteer else None,is_feasible=self.is_feasible,notes=self.notes,pickup_distance_km=self.pickup_distance_km)

def volunteer_candidates(resource, request, now=None, reserved_quantity=0):
    if reserved_quantity:
        from copy import copy
        resource, request = copy(resource), copy(request)
        if resource.status == 'RESERVED':
            resource.status = 'AVAILABLE'
        resource.allocated_quantity = max(0, resource.allocated_quantity - reserved_quantity)
        if request.status in ['ALLOCATED', 'PARTIALLY_ALLOCATED']:
            request.status = 'OPEN'
        request.fulfilled_quantity = max(0, request.fulfilled_quantity - reserved_quantity)
    now=now or timezone.now()
    eligibility=evaluate_resource_request_eligibility(resource,request,now)
    if not eligibility.is_eligible: return [], eligibility.reasons_rejected
    weight=1.0 if resource.unit=='kg' else resource.unit_weight_kg
    if weight is None or not math.isfinite(weight) or weight<=0:
        return [], [f'Missing recorded kg-per-{resource.unit} weight; volunteer capacity cannot be verified.']
    volunteers=Volunteer.objects.filter(verified=True,status='available',user__is_active=True,user__status='active',user__role_assignments__role='VOLUNTEER',user__role_assignments__is_approved=True).select_related('user').distinct()
    candidates=[]; rejected=[]
    for vol in volunteers:
        if vol.delivery_tasks.exclude(status__in=['DELIVERED','CANCELLED','DECLINED']).exists() or vol.food_claims.filter(status__in=['ASSIGNED','PICKED_UP']).exists():
            rejected.append(f'{vol.pk}: already has an active delivery.'); continue
        capacity=vol.vehicle_capacity_kg/weight
        minimum = 1 if resource.unit in ['meals','kits','items','packs','portions','bottles','boxes','packages'] else .01
        if not math.isfinite(capacity) or capacity < minimum or eligibility.compatible_quantity < minimum:
            rejected.append(f'{vol.pk}: no positive recorded vehicle capacity.'); continue
        distance,kind=recorded_distance(vol.latitude,vol.longitude,*resource_coordinates(resource))
        if distance is None or distance>MAX_SERVICE_RADIUS_KM:
            rejected.append(f'{vol.pk}: pickup location missing or outside service radius.'); continue
        warnings=list(eligibility.missing_information)
        if resource.storage_requirements!='Ambient':
            if vol.transport_storage is None:
                rejected.append(f'{vol.pk}: missing verified transport storage for {resource.storage_requirements}.'); continue
            if resource.storage_requirements not in vol.transport_storage:
                rejected.append(f'{vol.pk}: transport storage incompatible with {resource.storage_requirements}.'); continue
        pickup=eligibility.pickup_at
        if vol.travel_speed_kmh is not None:
            if not math.isfinite(vol.travel_speed_kmh) or vol.travel_speed_kmh<=0:
                rejected.append(f'{vol.pk}: invalid recorded travel speed.'); continue
            pickup=max(pickup,now+timedelta(hours=distance/vol.travel_speed_kmh))
            arrival=pickup+timedelta(hours=eligibility.distance_km/vol.travel_speed_kmh)
            windows=receiving_intervals(request.recipient,arrival,eligibility.delivery_by)
            if pickup>=resource.pickup_end or arrival>=eligibility.delivery_by or windows==[]:
                rejected.append(f'{vol.pk}: recorded travel estimate misses pickup, receiving hours or safe-consumption deadline.'); continue
            warnings.append('Transit uses recorded speed and straight-line distance; road conditions and handling time require confirmation.')
        else:
            warnings.append(f'{vol.pk}: travel speed/time is not recorded; route timing requires coordinator confirmation.')
        candidates.append(dict(volunteer=vol,capacity=math.floor((capacity+1e-9)*100)/100,pickup_distance_km=distance,missing_information=warnings,distance_type=kind))
    if not candidates and not rejected: rejected=['No verified, available, eligible volunteers with an approved role.']
    return sorted(candidates,key=lambda c:(c['pickup_distance_km'],c['volunteer'].pk)),rejected

def match_volunteer_for_allocation(resource, request, allocated_quantity, assigned_volunteer_ids=None, reserved_quantity=0):
    candidates,reasons=volunteer_candidates(resource,request,reserved_quantity=reserved_quantity)
    assigned_volunteer_ids=assigned_volunteer_ids if assigned_volunteer_ids is not None else set()
    for candidate in candidates:
        vol=candidate['volunteer']
        if vol.pk in assigned_volunteer_ids or candidate['capacity']<allocated_quantity: continue
        assigned_volunteer_ids.add(vol.pk)
        return VolunteerAssignmentResult(vol,True,f'Verified courier {vol.full_name}; capacity {candidate["capacity"]} {resource.unit}; straight-line pickup distance {candidate["pickup_distance_km"]} km. '+ ' '.join(candidate['missing_information']),candidate['pickup_distance_km'])
    return VolunteerAssignmentResult(None,False,' '.join(reasons) or 'Available couriers cannot carry this quantity or are reserved by another mission.')
