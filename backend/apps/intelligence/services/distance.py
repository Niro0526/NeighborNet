import math
from typing import Dict, Any, Optional

# Moratuwa & Colombo South Pilot Region Center & Bounds
MORATUWA_LAT = 6.7730
MORATUWA_LON = 79.8816
MAX_SERVICE_RADIUS_KM = 35.0  # Max realistic volunteer delivery radius across Colombo South / Western Province


def valid_coordinates(lat, lon):
    return lat is not None and lon is not None and math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180


def resource_coordinates(resource):
    if resource.pickup_latitude is not None or resource.pickup_longitude is not None:
        return resource.pickup_latitude, resource.pickup_longitude
    if resource.pickup_address.strip() and resource.pickup_address.strip().casefold() != resource.provider.address.strip().casefold():
        return None, None
    return resource.provider.latitude, resource.provider.longitude


def request_coordinates(request):
    if request.delivery_latitude is not None or request.delivery_longitude is not None:
        return request.delivery_latitude, request.delivery_longitude
    if request.delivery_address.strip() and request.delivery_address.strip().casefold() != request.recipient.address.strip().casefold():
        return None, None
    return request.recipient.latitude, request.recipient.longitude


def recorded_distance(lat1, lon1, lat2, lon2):
    """Never manufacture coordinates or distances for unknown locations."""
    if not valid_coordinates(lat1, lon1) or not valid_coordinates(lat2, lon2):
        return None, 'unknown'
    from django.db import connection
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis')")
            if cursor.fetchone()[0]:
                cursor.execute('SELECT ST_DistanceSphere(ST_MakePoint(%s,%s), ST_MakePoint(%s,%s))/1000', [lon1, lat1, lon2, lat2])
                return round(float(cursor.fetchone()[0]), 2), 'straight_line_postgis'
    return calculate_haversine_distance(lat1, lon1, lat2, lon2), 'straight_line_haversine'

def calculate_haversine_distance(
    lat1: Optional[float], lon1: Optional[float],
    lat2: Optional[float], lon2: Optional[float]
) -> float:
    """
    Computes straight-line great-circle distance in kilometers using the Haversine formula.
    Explicitly labeled as 'straight_line_haversine' to prevent confusing it with road navigation.
    """
    if not valid_coordinates(lat1, lon1) or not valid_coordinates(lat2, lon2):
        raise ValueError('Cannot estimate distance without valid recorded coordinates.')

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
        return False
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
