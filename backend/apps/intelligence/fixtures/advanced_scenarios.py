import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Tuple, Dict, Any
from apps.organizations.models import Organization, OrganizationTypeChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices, StorageRequirementChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices, VehicleTypeChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices, DisasterSeverityChoices

ADVANCED_SUITE_ID = "MODELX_EVAL_ADVANCED_V1"
ADVANCED_REFERENCE_TIMESTAMP = datetime(2026, 10, 15, 12, 0, 0, tzinfo=dt_timezone.utc)

def get_or_create_org(org_id: str, name: str, org_type: str, verified: bool, lat: float, lon: float) -> Organization:
    org, _ = Organization.objects.get_or_create(
        id=org_id,
        defaults={
            'name': name,
            'type': org_type,
            'verified': verified,
            'contact_email': f"info@{org_id.lower()}.org",
            'contact_phone': "+94112000000",
            'address': f"Advanced Location, {name}",
            'city': 'Moratuwa',
            'latitude': lat,
            'longitude': lon,
        }
    )
    org.verified = verified
    org.latitude = lat
    org.longitude = lon
    org.save()
    return org

def get_advanced_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    Returns deterministic synthetic fixtures for one of the 7 advanced evaluation scenarios.
    Suite ID: MODELX_EVAL_ADVANCED_V1
    """
    ref_time = ADVANCED_REFERENCE_TIMESTAMP

    p1 = get_or_create_org("ADV-ORG-P1", "Moratuwa Central Kitchen", OrganizationTypeChoices.COMMUNITY_KITCHEN, True, 6.773, 79.881)
    p2 = get_or_create_org("ADV-ORG-P2", "Colombo South Depot", OrganizationTypeChoices.SUPERMARKET, True, 6.830, 79.865)

    r1 = get_or_create_org("ADV-ORG-R1", "Hope Relief Center", OrganizationTypeChoices.NGO, True, 6.778, 79.885)
    r2 = get_or_create_org("ADV-ORG-R2", "Grace Elder Care", OrganizationTypeChoices.NGO, True, 6.818, 79.875)

    if scenario_id == '1_COMPETING_EXPIRY':
        # Scenario 1: Perishable 3h expiry vs 24h expiry competing for 50kg demand
        res_perishable = Resource(
            id="ADV-RES-S1-A", provider=p1, name="Prepared Meals (3h Left)",
            category=ResourceCategoryChoices.COOKED_MEALS, quantity=50.0, unit="kg",
            pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=3),
            safe_until=ref_time + timedelta(hours=4), storage_requirements=StorageRequirementChoices.KEEP_WARM,
            status=ResourceStatusChoices.AVAILABLE
        )
        res_stable = Resource(
            id="ADV-RES-S1-B", provider=p1, name="Prepared Meals (24h Left)",
            category=ResourceCategoryChoices.COOKED_MEALS, quantity=50.0, unit="kg",
            pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=12),
            safe_until=ref_time + timedelta(hours=24), storage_requirements=StorageRequirementChoices.KEEP_WARM,
            status=ResourceStatusChoices.AVAILABLE
        )
        req = ResourceRequest(
            id="ADV-REQ-S1", recipient=r1, item_name="Meal Rations",
            category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=50.0, unit="kg",
            priority=RequestPriorityChoices.HIGH, urgency_deadline=ref_time + timedelta(hours=5),
            created_at=ref_time - timedelta(hours=1)
        )
        return {
            'scenario_name': '1. Competing Food-Expiry Deadlines',
            'purpose': 'Verify solver prioritizes short shelf-life perishable food (3h left) over stable food (24h left) to prevent waste.',
            'resources': [res_perishable, res_stable],
            'requests': [req],
            'volunteers': [],
            'ref_time': ref_time,
            'provenance': 'SYNTHETIC_ADVANCED_FIXTURE_V1'
        }

    elif scenario_id == '2_INSUFFICIENT_VOLUNTEER_CAPACITY':
        # Scenario 2: Heavy 150kg bulk cargo vs 15kg bicycle volunteer
        res_heavy = Resource(
            id="ADV-RES-S2", provider=p1, name="Bulk Rice Rations",
            category=ResourceCategoryChoices.COOKED_MEALS, quantity=150.0, unit="kg",
            pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=5),
            safe_until=ref_time + timedelta(hours=12), storage_requirements=StorageRequirementChoices.AMBIENT,
            status=ResourceStatusChoices.AVAILABLE
        )
        req_heavy = ResourceRequest(
            id="ADV-REQ-S2", recipient=r1, item_name="Bulk Meals",
            category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=150.0, unit="kg",
            priority=RequestPriorityChoices.URGENT, urgency_deadline=ref_time + timedelta(hours=6),
            created_at=ref_time - timedelta(hours=1)
        )
        return {
            'scenario_name': '2. Insufficient Volunteer Carrying Capacity',
            'purpose': 'Verify Stage 2 courier staging flags 150kg payload as logistically infeasible for 15kg bicycle courier.',
            'resources': [res_heavy],
            'requests': [req_heavy],
            'volunteers': [],
            'ref_time': ref_time,
            'provenance': 'SYNTHETIC_ADVANCED_FIXTURE_V1'
        }

    elif scenario_id == '3_OVERLAPPING_SCHEDULES':
        # Scenario 3: Two overlapping requests at 14:00
        res_a = Resource(id="ADV-RES-S3-A", provider=p1, name="Meals A", category=ResourceCategoryChoices.COOKED_MEALS, quantity=30.0, unit="kg", pickup_start=ref_time, pickup_end=ref_time + timedelta(hours=2), safe_until=ref_time + timedelta(hours=6), storage_requirements=StorageRequirementChoices.AMBIENT, status=ResourceStatusChoices.AVAILABLE)
        res_b = Resource(id="ADV-RES-S3-B", provider=p2, name="Meals B", category=ResourceCategoryChoices.COOKED_MEALS, quantity=30.0, unit="kg", pickup_start=ref_time, pickup_end=ref_time + timedelta(hours=2), safe_until=ref_time + timedelta(hours=6), storage_requirements=StorageRequirementChoices.AMBIENT, status=ResourceStatusChoices.AVAILABLE)

        req_a = ResourceRequest(id="ADV-REQ-S3-A", recipient=r1, item_name="Meals Demand A", category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=30.0, unit="kg", priority=RequestPriorityChoices.HIGH, urgency_deadline=ref_time + timedelta(hours=3), created_at=ref_time - timedelta(hours=1))
        req_b = ResourceRequest(id="ADV-REQ-S3-B", recipient=r2, item_name="Meals Demand B", category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=30.0, unit="kg", priority=RequestPriorityChoices.HIGH, urgency_deadline=ref_time + timedelta(hours=3), created_at=ref_time - timedelta(hours=1))

        return {
            'scenario_name': '3. Overlapping Delivery Schedules',
            'purpose': 'Verify conflict resolution prevents assigning single courier to simultaneous pickup windows.',
            'resources': [res_a, res_b],
            'requests': [req_a, req_b],
            'volunteers': [],
            'ref_time': ref_time,
            'provenance': 'SYNTHETIC_ADVANCED_FIXTURE_V1'
        }

    elif scenario_id == '4_UNEVEN_PRIORITIES':
        # Scenario 4: 50kg supply vs Urgent (50kg) and Low (50kg) requests
        res = Resource(id="ADV-RES-S4", provider=p1, name="Rations", category=ResourceCategoryChoices.COOKED_MEALS, quantity=50.0, unit="kg", pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=5), safe_until=ref_time + timedelta(hours=10), storage_requirements=StorageRequirementChoices.AMBIENT, status=ResourceStatusChoices.AVAILABLE)
        req_low = ResourceRequest(id="ADV-REQ-S4-LOW", recipient=r1, item_name="Low Priority Rations", category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=50.0, unit="kg", priority=RequestPriorityChoices.LOW, urgency_deadline=ref_time + timedelta(hours=8), created_at=ref_time - timedelta(hours=2))
        req_urgent = ResourceRequest(id="ADV-REQ-S4-URGENT", recipient=r2, item_name="Emergency Relief Meals", category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=50.0, unit="kg", priority=RequestPriorityChoices.URGENT, urgency_deadline=ref_time + timedelta(hours=4), created_at=ref_time - timedelta(hours=1))

        return {
            'scenario_name': '4. Uneven Recipient Priorities',
            'purpose': 'Verify CP-SAT solver allocates 50kg supply to URGENT priority request over LOW priority request regardless of chronological order.',
            'resources': [res],
            'requests': [req_low, req_urgent],
            'volunteers': [],
            'ref_time': ref_time,
            'provenance': 'SYNTHETIC_ADVANCED_FIXTURE_V1'
        }

    elif scenario_id == '5_DISASTER_SCARCITY':
        # Scenario 5: Disaster mode relief allocation under 60kg supply vs 100kg demand
        evt, _ = DisasterEvent.objects.get_or_create(id="EVT-ADV-DISASTER", defaults={'title': 'Monsoon Flood Disaster', 'disaster_type': 'FLOOD', 'severity': DisasterSeverityChoices.CRITICAL, 'status': DisasterStatusChoices.ACTIVE, 'affected_location': 'Moratuwa', 'declared_at': ref_time - timedelta(hours=12)})
        res = Resource(id="ADV-RES-S5", provider=p1, name="Disaster Water Rations", category=ResourceCategoryChoices.DRINKING_WATER, quantity=60.0, unit="liters", pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=8), safe_until=ref_time + timedelta(hours=48), storage_requirements=StorageRequirementChoices.AMBIENT, status=ResourceStatusChoices.AVAILABLE)
        req = ResourceRequest(id="ADV-REQ-S5", recipient=r1, item_name="Emergency Water Need", category=ResourceCategoryChoices.DRINKING_WATER, requested_quantity=100.0, unit="liters", priority=RequestPriorityChoices.URGENT, urgency_deadline=ref_time + timedelta(hours=6), is_disaster_relief=True, disaster_event_id=evt.id, created_at=ref_time - timedelta(hours=2))

        return {
            'scenario_name': '5. Disaster Resource Scarcity & Priority',
            'purpose': 'Verify CP-SAT allocates 60L available water under disaster mode constraints, leaving 40L unmet demand recorded.',
            'resources': [res],
            'requests': [req],
            'volunteers': [],
            'ref_time': ref_time,
            'provenance': 'SYNTHETIC_ADVANCED_FIXTURE_V1'
        }

    elif scenario_id == '6_VOLUNTEER_CANCELLATION_RECOVERY':
        # Scenario 6: Volunteer cancellation recovery replanning
        res = Resource(id="ADV-RES-S6", provider=p1, name="Rescue Packs", category=ResourceCategoryChoices.COOKED_MEALS, quantity=40.0, unit="kg", pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=5), safe_until=ref_time + timedelta(hours=12), storage_requirements=StorageRequirementChoices.AMBIENT, status=ResourceStatusChoices.AVAILABLE)
        req = ResourceRequest(id="ADV-REQ-S6", recipient=r1, item_name="Rescue Packs Request", category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=40.0, unit="kg", priority=RequestPriorityChoices.HIGH, urgency_deadline=ref_time + timedelta(hours=6), created_at=ref_time - timedelta(hours=1))

        return {
            'scenario_name': '6. Volunteer Cancellation & Recovery Replanning',
            'purpose': 'Verify disruption engine recomputes replacement courier assignment upon volunteer cancellation.',
            'resources': [res],
            'requests': [req],
            'volunteers': [],
            'ref_time': ref_time,
            'provenance': 'SYNTHETIC_ADVANCED_FIXTURE_V1'
        }

    elif scenario_id == '7_MIXED_UNITS_ISOLATION':
        # Scenario 7: Mixed units (kg, liters, kits, boxes)
        res_kg = Resource(id="ADV-RES-S7-KG", provider=p1, name="Rice Rations", category=ResourceCategoryChoices.COOKED_MEALS, quantity=50.0, unit="kg", pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=5), safe_until=ref_time + timedelta(hours=12), storage_requirements=StorageRequirementChoices.AMBIENT, status=ResourceStatusChoices.AVAILABLE)
        res_l = Resource(id="ADV-RES-S7-L", provider=p2, name="Water Cans", category=ResourceCategoryChoices.DRINKING_WATER, quantity=30.0, unit="liters", pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=5), safe_until=ref_time + timedelta(hours=48), storage_requirements=StorageRequirementChoices.AMBIENT, status=ResourceStatusChoices.AVAILABLE)
        res_kits = Resource(id="ADV-RES-S7-KITS", provider=p2, name="Hygiene Kits", category=ResourceCategoryChoices.HYGIENE_KITS, quantity=20.0, unit="kits", pickup_start=ref_time - timedelta(hours=1), pickup_end=ref_time + timedelta(hours=5), safe_until=ref_time + timedelta(hours=72), storage_requirements=StorageRequirementChoices.AMBIENT, status=ResourceStatusChoices.AVAILABLE)

        req_kg = ResourceRequest(id="ADV-REQ-S7-KG", recipient=r1, item_name="Meals Need", category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=50.0, unit="kg", priority=RequestPriorityChoices.HIGH, urgency_deadline=ref_time + timedelta(hours=6), created_at=ref_time - timedelta(hours=1))
        req_l = ResourceRequest(id="ADV-REQ-S7-L", recipient=r1, item_name="Water Need", category=ResourceCategoryChoices.DRINKING_WATER, requested_quantity=30.0, unit="liters", priority=RequestPriorityChoices.HIGH, urgency_deadline=ref_time + timedelta(hours=6), created_at=ref_time - timedelta(hours=1))
        req_kits = ResourceRequest(id="ADV-REQ-S7-KITS", recipient=r2, item_name="Kits Need", category=ResourceCategoryChoices.HYGIENE_KITS, requested_quantity=20.0, unit="kits", priority=RequestPriorityChoices.MEDIUM, urgency_deadline=ref_time + timedelta(hours=6), created_at=ref_time - timedelta(hours=1))
        req_boxes = ResourceRequest(id="ADV-REQ-S7-BOXES", recipient=r2, item_name="Boxes Need", category=ResourceCategoryChoices.COOKED_MEALS, requested_quantity=10.0, unit="boxes", priority=RequestPriorityChoices.LOW, urgency_deadline=ref_time + timedelta(hours=6), created_at=ref_time - timedelta(hours=1))

        return {
            'scenario_name': '7. Mixed Unit Isolation & Conservation',
            'purpose': 'Verify strict unit isolation: kg, liters, and kits allocate in exact respective units, and boxes is rejected without cross-unit summing.',
            'resources': [res_kg, res_l, res_kits],
            'requests': [req_kg, req_l, req_kits, req_boxes],
            'volunteers': [],
            'ref_time': ref_time,
            'provenance': 'SYNTHETIC_ADVANCED_FIXTURE_V1'
        }

    else:
        raise ValueError(f"Unknown advanced scenario ID: {scenario_id}")

ALL_ADVANCED_SCENARIO_IDS = [
    '1_COMPETING_EXPIRY',
    '2_INSUFFICIENT_VOLUNTEER_CAPACITY',
    '3_OVERLAPPING_SCHEDULES',
    '4_UNEVEN_PRIORITIES',
    '5_DISASTER_SCARCITY',
    '6_VOLUNTEER_CANCELLATION_RECOVERY',
    '7_MIXED_UNITS_ISOLATION',
]
