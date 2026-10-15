from typing import List, Dict, Any, Optional
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from .distance import calculate_haversine_distance

class VolunteerAssignmentResult:
    def __init__(
        self,
        volunteer: Optional[Volunteer],
        is_feasible: bool,
        notes: str,
        pickup_distance_km: float = 0.0,
    ):
        self.volunteer = volunteer
        self.is_feasible = is_feasible
        self.notes = notes
        self.pickup_distance_km = pickup_distance_km

    def to_dict(self) -> Dict[str, Any]:
        return {
            'volunteer_id': self.volunteer.id if self.volunteer else None,
            'volunteer_name': self.volunteer.full_name if self.volunteer else None,
            'vehicle_type': self.volunteer.vehicle_type if self.volunteer else None,
            'vehicle_capacity_kg': self.volunteer.vehicle_capacity_kg if self.volunteer else None,
            'is_feasible': self.is_feasible,
            'notes': self.notes,
            'pickup_distance_km': self.pickup_distance_km,
        }

def match_volunteer_for_allocation(
    resource: Resource,
    request: ResourceRequest,
    allocated_quantity: float,
    assigned_volunteer_ids: Optional[set] = None
) -> VolunteerAssignmentResult:
    """
    Second-Stage Logistics Feasibility Engine:
    Finds the closest verified, available courier whose vehicle carrying capacity
    satisfies the allocated load without overlapping task conflicts.
    """
    if assigned_volunteer_ids is None:
        assigned_volunteer_ids = set()

    # Query active, verified volunteers
    volunteers = Volunteer.objects.filter(
        status=VolunteerAvailabilityChoices.AVAILABLE,
        verified=True
    ).exclude(id__in=assigned_volunteer_ids)

    if not volunteers.exists():
        return VolunteerAssignmentResult(
            volunteer=None,
            is_feasible=False,
            notes="Logistics Warning: No verified volunteers currently AVAILABLE in this operating sector.",
        )

    res_lat = getattr(resource.provider, 'latitude', None)
    res_lon = getattr(resource.provider, 'longitude', None)

    candidates = []
    for vol in volunteers:
        # Check capacity
        if vol.vehicle_capacity_kg < allocated_quantity:
            continue

        vol_lat = vol.latitude
        vol_lon = vol.longitude
        dist_to_pickup = calculate_haversine_distance(vol_lat, vol_lon, res_lat, res_lon)

        candidates.append((dist_to_pickup, vol))

    if not candidates:
        return VolunteerAssignmentResult(
            volunteer=None,
            is_feasible=False,
            notes=f"Logistics Warning: Cargo load ({allocated_quantity} {resource.unit}) exceeds vehicle capacities of currently available volunteers.",
        )

    # Pick the closest courier to donor pickup location
    candidates.sort(key=lambda c: c[0])
    best_dist, best_volunteer = candidates[0]

    assigned_volunteer_ids.add(best_volunteer.id)

    notes = (
        f"Verified Courier {best_volunteer.full_name} ({best_volunteer.get_vehicle_type_display()}, "
        f"capacity: {best_volunteer.vehicle_capacity_kg} kg) assigned. "
        f"Pickup staging distance: {best_dist} km."
    )

    return VolunteerAssignmentResult(
        volunteer=best_volunteer,
        is_feasible=True,
        notes=notes,
        pickup_distance_km=best_dist,
    )
