from datetime import timedelta
from typing import Dict, Any, List, Tuple
from django.utils import timezone
from apps.resources.models import Resource, ResourceStatusChoices, ResourceCategoryChoices
from apps.requests.models import ResourceRequest, RequestStatusChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices
from .distance import calculate_haversine_distance, MAX_SERVICE_RADIUS_KM

# Category Compatibility Matrix: What resource categories can safely satisfy request categories
COMPATIBILITY_MATRIX: Dict[str, List[str]] = {
    ResourceCategoryChoices.COOKED_MEALS: [
        ResourceCategoryChoices.COOKED_MEALS,
        ResourceCategoryChoices.BAKERY,  # Bakery bread/pastries can support meal feeding
    ],
    ResourceCategoryChoices.BAKERY: [
        ResourceCategoryChoices.BAKERY,
    ],
    ResourceCategoryChoices.FRESH_PRODUCE: [
        ResourceCategoryChoices.FRESH_PRODUCE,
    ],
    ResourceCategoryChoices.DAIRY: [
        ResourceCategoryChoices.DAIRY,
    ],
    ResourceCategoryChoices.CANNED_PACKAGED: [
        ResourceCategoryChoices.CANNED_PACKAGED,
    ],
    ResourceCategoryChoices.DRINKING_WATER: [
        ResourceCategoryChoices.DRINKING_WATER,
    ],
    ResourceCategoryChoices.BEVERAGES: [
        ResourceCategoryChoices.BEVERAGES,
    ],
    ResourceCategoryChoices.HYGIENE_KITS: [
        ResourceCategoryChoices.HYGIENE_KITS,
    ],
    ResourceCategoryChoices.BLANKETS_BEDDING: [
        ResourceCategoryChoices.BLANKETS_BEDDING,
    ],
    ResourceCategoryChoices.MEDICAL_SUPPLIES: [
        ResourceCategoryChoices.MEDICAL_SUPPLIES,
    ],
}

def is_category_compatible(resource_category: str, request_category: str) -> bool:
    """Checks if a resource category is compatible with a requested category."""
    if resource_category == request_category:
        return True
    compatible = COMPATIBILITY_MATRIX.get(request_category, [request_category])
    return resource_category in compatible

class EligibilityResult:
    def __init__(
        self,
        is_eligible: bool,
        reasons_rejected: List[str],
        constraints_satisfied: List[str],
        distance_km: float,
        compatible_quantity: float,
    ):
        self.is_eligible = is_eligible
        self.reasons_rejected = reasons_rejected
        self.constraints_satisfied = constraints_satisfied
        self.distance_km = distance_km
        self.compatible_quantity = compatible_quantity

    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_eligible': self.is_eligible,
            'reasons_rejected': self.reasons_rejected,
            'constraints_satisfied': self.constraints_satisfied,
            'distance_km': self.distance_km,
            'compatible_quantity': self.compatible_quantity,
        }

def evaluate_resource_request_eligibility(
    resource: Resource,
    request: ResourceRequest,
    now=None
) -> EligibilityResult:
    """
    Evaluates mandatory hard constraints for matching an available resource lot to a recipient request.
    Strictly deterministic. Does not use LLMs or heuristic guesses for food safety.
    """
    if now is None:
        now = timezone.now()

    reasons: List[str] = []
    satisfied: List[str] = []

    # 1. Resource Availability & State
    if resource.status != ResourceStatusChoices.AVAILABLE:
        reasons.append(f"Resource status is '{resource.status}' (must be AVAILABLE).")
    else:
        satisfied.append("Resource status is AVAILABLE.")

    if resource.available_quantity <= 0:
        reasons.append(f"Resource has 0 available inventory (allocated: {resource.allocated_quantity}/{resource.quantity}).")
    else:
        satisfied.append(f"Resource has {resource.available_quantity} {resource.unit} available.")

    # 2. Food Safety & Expiry Deadlines
    if resource.safe_until and resource.safe_until <= now + timedelta(hours=2):
        reasons.append(f"Resource expired or safe-use deadline expires in less than 2 hours (deadline: {resource.safe_until.strftime('%Y-%m-%d %H:%M')}).")
    else:
        satisfied.append("Resource safe-use deadline is unexpired (>= 2h remaining).")

    if resource.pickup_end and resource.pickup_end <= now:
        reasons.append(f"Pickup window closed on {resource.pickup_end.strftime('%Y-%m-%d %H:%M')}.")
    else:
        satisfied.append("Pickup window is currently open.")

    if not resource.storage_requirements:
        reasons.append("Missing food storage requirements information.")
    else:
        satisfied.append(f"Food safety storage condition documented: {resource.storage_requirements}.")

    # 3. Category & Unit Compatibility
    if not is_category_compatible(resource.category, request.category):
        reasons.append(f"Category mismatch: Resource is '{resource.category}' while Request needs '{request.category}'.")
    else:
        satisfied.append(f"Category compatible ({resource.category} -> {request.category}).")

    if resource.unit != request.unit:
        reasons.append(f"Unit mismatch: Resource uses '{resource.unit}' while Request uses '{request.unit}'.")
    else:
        satisfied.append(f"Units matched ({resource.unit}).")

    # 4. Organization Verification Requirements
    if not resource.provider.verified:
        reasons.append(f"Provider organization '{resource.provider.name}' is unverified.")
    else:
        satisfied.append("Provider organization is officially verified.")

    if not request.recipient.verified:
        # Emergency relief exemption only if explicitly marked and emergency
        if request.is_disaster_relief:
            satisfied.append("Recipient unverified but granted temporary disaster shelter clearance.")
        else:
            reasons.append(f"Recipient organization '{request.recipient.name}' is unverified.")
    else:
        satisfied.append("Recipient organization is officially verified.")

    # 5. Timing Feasibility
    if resource.pickup_start > request.urgency_deadline:
        reasons.append(
            f"Pickup start ({resource.pickup_start.strftime('%H:%M')}) is after request urgency deadline ({request.urgency_deadline.strftime('%H:%M')})."
        )
    else:
        satisfied.append("Pickup start is feasible within recipient deadline.")

    # 6. Disaster Mode Constraints
    if request.is_disaster_relief:
        if not request.disaster_event_id:
            reasons.append("Disaster relief request is missing linked Disaster Event ID.")
        else:
            event = DisasterEvent.objects.filter(id=request.disaster_event_id).first()
            if not event or event.status != DisasterStatusChoices.ACTIVE:
                reasons.append("Referenced Disaster Event is not currently ACTIVE.")
            else:
                satisfied.append(f"Disaster Event '{event.title}' is verified ACTIVE.")

    # 7. Geographic Distance Check
    prov_lat = getattr(resource.provider, 'latitude', None)
    prov_lon = getattr(resource.provider, 'longitude', None)
    rec_lat = getattr(request.recipient, 'latitude', None)
    rec_lon = getattr(request.recipient, 'longitude', None)

    distance_km = calculate_haversine_distance(prov_lat, prov_lon, rec_lat, rec_lon)
    if distance_km > MAX_SERVICE_RADIUS_KM:
        reasons.append(f"Geographic distance ({distance_km} km) exceeds maximum pilot delivery radius ({MAX_SERVICE_RADIUS_KM} km).")
    else:
        satisfied.append(f"Geographic distance ({distance_km} km) is within service zone ({MAX_SERVICE_RADIUS_KM} km).")

    # 8. Quantity Eligibility
    compatible_quantity = min(resource.available_quantity, request.remaining_quantity)
    if compatible_quantity <= 0:
        reasons.append("No mutually compatible quantity available.")

    is_eligible = len(reasons) == 0
    return EligibilityResult(
        is_eligible=is_eligible,
        reasons_rejected=reasons,
        constraints_satisfied=satisfied,
        distance_km=distance_km,
        compatible_quantity=compatible_quantity,
    )
