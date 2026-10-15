from typing import Dict, Any, List
from django.utils import timezone

def format_allocation_explanation(
    resource_name: str,
    recipient_name: str,
    quantity: float,
    unit: str,
    distance_km: float,
    priority: str,
    solver_status: str,
    constraints_satisfied: List[str],
    volunteer_name: str = None
) -> Dict[str, Any]:
    """
    Constructs a transparent, deterministic audit explanation for a recommended allocation.
    Never fabricates ML confidence scores for mathematical optimization.
    """
    courier_note = f" Volunteer courier '{volunteer_name}' assigned." if volunteer_name else " Volunteer courier unassigned (pending staging)."

    summary_text = (
        f"Allocate {quantity} {unit} of '{resource_name}' to '{recipient_name}'. "
        f"Matches verified category requirements with feasible timing, shelf-life safety, "
        f"and geographic proximity of {distance_km} km.{courier_note}"
    )

    suggested_action = (
        f"Submit for Coordinator authorization. Once approved, commits {quantity} {unit} "
        f"to reserve supply and dispatch delivery task."
    )

    return {
        'summary': summary_text,
        'suggested_action': suggested_action,
        'operational_impact': f"Fulfills {quantity} {unit} demand for {priority.upper()} priority requisition.",
        'solver_status': solver_status,
        'constraints_verified': constraints_satisfied,
        'limitations_and_uncertainty': (
            "Proximity is straight-line Haversine distance. Actual road navigation depends on "
            "driver travel conditions and local flood advisories."
        ),
    }
