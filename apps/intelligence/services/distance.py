import math
from typing import Dict, Any, Optional

# Moratuwa & Colombo South Pilot Region Center & Bounds
MORATUWA_LAT = 6.7730
MORATUWA_LON = 79.8816
MAX_SERVICE_RADIUS_KM = 35.0  # Max realistic volunteer delivery radius across Colombo South / Western Province

def calculate_haversine_distance(
    lat1: Optional[float], lon1: Optional[float],
    lat2: Optional[float], lon2: Optional[float]
) -> float:
    """
    Computes straight-line great-circle distance in kilometers using the Haversine formula.
    Explicitly labeled as 'straight_line_haversine' to prevent confusing it with road navigation.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 5.0  # Default conservative local estimate within pilot city if coordinates missing

    # Convert degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    earth_radius_km = 6371.0
    dist = earth_radius_km * c
    return round(dist, 2)

def is_within_service_area(lat: Optional[float], lon: Optional[float]) -> bool:
    """
    Validates if a coordinate is within the pilot service zone (Colombo South & Western Province basin).
    """
    if lat is None or lon is None:
        return True  # Fallback to organization address validation
    dist = calculate_haversine_distance(MORATUWA_LAT, MORATUWA_LON, lat, lon)
    return dist <= MAX_SERVICE_RADIUS_KM

def get_distance_metadata(distance_km: float) -> Dict[str, Any]:
    """
    Returns transparency metadata declaring source and estimation bounds.
    """
    return {
        'distance_km': distance_km,
        'distance_type': 'straight_line_haversine',
        'is_road_network': False,
        'pilot_region': 'Moratuwa & Colombo South Lowlands',
        'disclaimer': 'Straight-line spatial proximity. Verified road navigation requires local driver check.',
    }
