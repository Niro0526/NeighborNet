"""Deterministic screening against recorded supply, NGO demand and verified preferences."""
import math
import re
from datetime import timedelta, datetime, time
from django.utils import timezone
from apps.disasters.models import DisasterEvent
from .distance import recorded_distance, resource_coordinates, request_coordinates, MAX_SERVICE_RADIUS_KM

# Cross-category substitutions require an explicit domain policy; none is recorded.
COMPATIBILITY_MATRIX = {}
def is_category_compatible(resource_category, request_category):
    return resource_category == request_category

class EligibilityResult:
    def __init__(self, is_eligible, reasons_rejected, constraints_satisfied, distance_km, compatible_quantity, missing_information=None, distance_type='unknown', pickup_at=None, delivery_by=None):
        self.is_eligible = is_eligible
        self.reasons_rejected = reasons_rejected
        self.constraints_satisfied = constraints_satisfied
        self.distance_km = distance_km
        self.compatible_quantity = compatible_quantity
        self.missing_information = missing_information or []
        self.distance_type = distance_type
        self.pickup_at = pickup_at
        self.delivery_by = delivery_by
    def to_dict(self):
        return {key: getattr(self,key) for key in ['is_eligible','reasons_rejected','constraints_satisfied','distance_km','compatible_quantity','missing_information','distance_type']}

def receiving_intervals(organization, start, end):
    text = organization.operating_hours.strip()
    if text.lower().startswith('24 hour') or text.lower() in ['24/7','24 hours','24h']:
        return [(start,end)]
    match = re.fullmatch(r'(\d{2}):(\d{2})\s*[-–]\s*(\d{2}):(\d{2})', text)
    if not match:
        return None
    h1,m1,h2,m2 = map(int,match.groups())
    if h1>23 or h2>23 or m1>59 or m2>59:
        return None
    local = timezone.localtime(start)
    tz = local.tzinfo
    windows=[]
    for offset in range(-1, min(370, (end-start).days+2)):
        day=local.date()+timedelta(days=offset)
        a=datetime.combine(day,time(h1,m1),tzinfo=tz)
        b=datetime.combine(day,time(h2,m2),tzinfo=tz)
        if b<=a: b+=timedelta(days=1)
        if max(a,start)<min(b,end): windows.append((max(a,start),min(b,end)))
    return windows

def evaluate_resource_request_eligibility(resource, request, now=None):
    now=now or timezone.now()
    reasons=[]; satisfied=[]; missing=[]
    if resource.status!='AVAILABLE': reasons.append(f'Resource status is {resource.status}; must be AVAILABLE.')
    if request.status not in ['OPEN','PARTIALLY_ALLOCATED']: reasons.append(f'Request status is {request.status}; no open demand.')
    quantities=[resource.quantity,resource.allocated_quantity,request.requested_quantity,request.fulfilled_quantity]
    if not all(math.isfinite(q) and q>=0 for q in quantities) or resource.allocated_quantity>resource.quantity or request.fulfilled_quantity>request.requested_quantity:
        reasons.append('Invalid recorded inventory or demand quantities.')
    elif any(abs(q-round(q,2))>1e-9 for q in quantities):
        reasons.append('Recorded quantities exceed the supported two decimal places; correct measurement precision before allocation.')
    quantity=min(resource.available_quantity,request.remaining_quantity)
    if not (resource.pickup_address or resource.provider.address).strip():
        missing.append('Provider pickup address is missing; coordinates are used for distance only.')
    if not (request.delivery_address or request.recipient.address).strip():
        missing.append('Recipient delivery address is missing; coordinates are used for distance only.')
    if quantity<=0: reasons.append('No mutually compatible quantity available.')
    if not request.allow_partial:
        satisfied.append('All-or-nothing demand: optimizer must fulfill the entire remaining request across its selected allocations.')
    if resource.category!=request.category: reasons.append(f'Category mismatch: {resource.category} cannot satisfy {request.category}.')
    else: satisfied.append(f'Exact food category: {resource.category}.')
    if resource.unit!=request.unit: reasons.append(f'Unit mismatch: {resource.unit} versus {request.unit}; no conversion inferred.')
    else: satisfied.append(f'Consistent recorded unit: {resource.unit}.')
    if not resource.provider.verified: reasons.append('Provider organization is unverified.')
    if not request.recipient.verified and not request.is_disaster_relief: reasons.append('Recipient organization is unverified.')
    if resource.provider_id==request.recipient_id: reasons.append('Provider cannot satisfy its own organization request.')
    if request.created_by_id and (not request.created_by.is_active or request.created_by.status!='active'):
        reasons.append('Request creator account is inactive or suspended.')
    if resource.is_disaster_relief!=request.is_disaster_relief or resource.disaster_event_id!=request.disaster_event_id:
        reasons.append('Resource and request operating mode / disaster event mismatch.')
    if not request.is_disaster_relief and (resource.disaster_event_id or request.disaster_event_id):
        reasons.append('Normal community matching cannot allocate event-linked disaster supplies or demand.')
    if request.is_disaster_relief and not DisasterEvent.objects.filter(pk=request.disaster_event_id,status='ACTIVE').exists():
        reasons.append('Disaster Event is not currently ACTIVE.')
    if resource.pickup_end<=now or resource.pickup_end<=resource.pickup_start: reasons.append('Pickup window is closed or invalid.')
    if resource.safe_until and resource.pickup_start >= resource.safe_until:
        reasons.append('Pickup begins after the safe-consumption deadline.')
    if request.urgency_deadline<=now: reasons.append('Request delivery deadline has expired.')
    if resource.is_food and not resource.safe_until:
        missing.append('Food safe-consumption deadline is missing.'); reasons.append('Food safety cannot be verified without a safe-consumption deadline.')
    if resource.safe_until and resource.safe_until<=now+timedelta(hours=2): reasons.append('Food is expired or has less than two hours of safe shelf life remaining.')
    if not resource.storage_requirements: missing.append('Provider storage instructions are missing.'); reasons.append('Food storage instructions are missing.')
    else: satisfied.append(f'Recorded handling requirement: {resource.storage_requirements}.')
    org=request.recipient
    if not org.matching_preferences_verified:
        missing.append('NGO dietary and storage preferences have not been verified; no preferences inferred.')
    else:
        if org.dietary_requirements is None: missing.append('NGO dietary requirements are not recorded.')
        else:
            required={s.strip().casefold() for s in org.dietary_requirements}
            supplied={s.strip().casefold() for s in resource.dietary_tags}
            if not required.issubset(supplied): reasons.append('Dietary mismatch: missing required tags '+', '.join(sorted(required-supplied))+'.')
            else: satisfied.append('Verified recorded dietary requirements satisfied.')
        if org.storage_capabilities is None: missing.append('NGO storage capabilities are not recorded.')
        elif resource.storage_requirements not in org.storage_capabilities: reasons.append(f'Storage mismatch: recipient cannot handle {resource.storage_requirements}.')
        else: satisfied.append('Verified recipient storage capability matches.')
    distance,kind=recorded_distance(*resource_coordinates(resource),*request_coordinates(request))
    if distance is None:
        missing.append('Valid pickup or recipient delivery coordinates are missing.'); reasons.append('Geographic eligibility cannot be verified from recorded delivery locations.')
    elif distance>MAX_SERVICE_RADIUS_KM: reasons.append(f'Geographic distance {distance} km exceeds {MAX_SERVICE_RADIUS_KM} km service radius.')
    else: satisfied.append(f'{kind}: {distance} km within service radius; not a road route.')
    pickup_at=max(now,resource.pickup_start)
    delivery_by=min(request.urgency_deadline,resource.safe_until or request.urgency_deadline)
    intervals=receiving_intervals(org,pickup_at,delivery_by) if delivery_by>pickup_at else []
    if intervals is None:
        missing.append('Recipient receiving hours are missing or not a supported HH:MM - HH:MM / 24 Hours record.')
    elif not intervals: reasons.append('Pickup time, recipient receiving hours and safe delivery deadline do not overlap.')
    else:
        first=intervals[0]
        delivery_by=intervals[-1][1]
        satisfied.append('Recorded receiving hours overlap the pickup/delivery window (Asia/Colombo).')
    if pickup_at>=delivery_by: reasons.append('No time remains between feasible pickup and the delivery deadline.')
    return EligibilityResult(not reasons,reasons,satisfied,distance,quantity,missing,kind,pickup_at,delivery_by)
