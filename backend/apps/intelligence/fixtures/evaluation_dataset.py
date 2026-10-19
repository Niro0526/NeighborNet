import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Tuple, Dict, Any
from apps.organizations.models import Organization, OrganizationTypeChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices, StorageRequirementChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices, DisasterSeverityChoices

# Frozen evaluation reference timestamp (immutable benchmark reference)
EVALUATION_REFERENCE_TIMESTAMP = datetime(2026, 10, 15, 12, 0, 0, tzinfo=dt_timezone.utc)
EVALUATION_DATASET_ID = "MODELX_EVAL_BENCHMARK_V1"
EVALUATION_DATASET_HASH = "sha256-f8a92e1040cfc34ad884ea3610ec54ea12"

def get_or_create_org(org_id: str, name: str, org_type: str, verified: bool, lat: float, lon: float) -> Organization:
    org, _ = Organization.objects.get_or_create(
        id=org_id,
        defaults={
            'name': name,
            'type': org_type,
            'verified': verified,
            'contact_email': f"info@{org_id.lower()}.org",
            'contact_phone': "+94112000000",
            'address': f"Evaluation Location, {name}",
            'city': 'Moratuwa',
            'latitude': lat,
            'longitude': lon,
        }
    )
    # Ensure verified state and coordinates match fixture
    org.verified = verified
    org.latitude = lat
    org.longitude = lon
    org.save()
    return org

def get_frozen_evaluation_dataset(mode: str = 'NORMAL', scenario: str = 'BALANCED') -> Tuple[List[Resource], List[ResourceRequest], datetime]:
    """
    Returns an immutable, reproducible evaluation dataset snapshot.
    BALANCED scenario: 200.0 kg requested demand, 200.0 kg available supply.
    SCARCITY scenario: 200.0 kg requested demand, 140.0 kg available supply (tests priority optimization).
    Reference timestamp frozen at 2026-10-15 12:00:00 UTC.
    """
    ref_time = EVALUATION_REFERENCE_TIMESTAMP

    # 1. Standardized Organizations
    provider_1 = get_or_create_org("EVAL-ORG-P1", "GreenBites Bakery & Cafe", OrganizationTypeChoices.BAKERY, True, 6.773, 79.881)
    provider_2 = get_or_create_org("EVAL-ORG-P2", "Colombo South Supermarket", OrganizationTypeChoices.SUPERMARKET, True, 6.830, 79.865)
    provider_3 = get_or_create_org("EVAL-ORG-P3", "Unity Community Kitchen", OrganizationTypeChoices.COMMUNITY_KITCHEN, True, 6.815, 79.878)

    recipient_1 = get_or_create_org("EVAL-ORG-R1", "Hope Community Shelter", OrganizationTypeChoices.NGO, True, 6.778, 79.885)
    recipient_2 = get_or_create_org("EVAL-ORG-R2", "Grace Home for Elders", OrganizationTypeChoices.NGO, True, 6.818, 79.875)
    recipient_3 = get_or_create_org("EVAL-ORG-R3", "Salvation Relief Center", OrganizationTypeChoices.NGO, True, 6.835, 79.868)

    # 2. Resources (Total 200.0 kg in BALANCED, 140.0 kg in SCARCITY)
    res1_qty = 80.0 if scenario == 'BALANCED' else 40.0
    res2_qty = 60.0 if scenario == 'BALANCED' else 40.0
    res3_qty = 60.0 if scenario == 'BALANCED' else 60.0

    res1 = Resource(
        id="EVAL-RES-01",
        provider=provider_1,
        name="Hot Rice & Curry Meal Rations",
        category=ResourceCategoryChoices.COOKED_MEALS,
        quantity=res1_qty,
        allocated_quantity=0.0,
        unit="kg",
        pickup_start=ref_time - timedelta(hours=1),
        pickup_end=ref_time + timedelta(hours=5),
        safe_until=ref_time + timedelta(hours=8),
        storage_requirements=StorageRequirementChoices.KEEP_WARM,
        status=ResourceStatusChoices.AVAILABLE,
    )

    res2 = Resource(
        id="EVAL-RES-02",
        provider=provider_1,
        name="Fresh Bakery Bread & Rolls",
        category=ResourceCategoryChoices.BAKERY,
        quantity=res2_qty,
        allocated_quantity=0.0,
        unit="kg",
        pickup_start=ref_time - timedelta(hours=1),
        pickup_end=ref_time + timedelta(hours=10),
        safe_until=ref_time + timedelta(hours=18),
        storage_requirements=StorageRequirementChoices.AMBIENT,
        status=ResourceStatusChoices.AVAILABLE,
    )

    res3 = Resource(
        id="EVAL-RES-03",
        provider=provider_2,
        name="Assorted Fresh Vegetables & Fruits",
        category=ResourceCategoryChoices.FRESH_PRODUCE,
        quantity=res3_qty,
        allocated_quantity=0.0,
        unit="kg",
        pickup_start=ref_time - timedelta(hours=1),
        pickup_end=ref_time + timedelta(hours=12),
        safe_until=ref_time + timedelta(hours=36),
        storage_requirements=StorageRequirementChoices.REFRIGERATED,
        status=ResourceStatusChoices.AVAILABLE,
    )

    resources = [res1, res2, res3]

    # 3. Requests (Total 200.0 kg)
    is_disaster = (mode == 'DISASTER')
    disaster_event_id = None
    if is_disaster:
        evt, _ = DisasterEvent.objects.get_or_create(
            id="EVT-DISASTER-01",
            defaults={
                'title': 'Evaluation Benchmark Monsoon Floods',
                'disaster_type': 'FLOOD',
                'severity': DisasterSeverityChoices.CRITICAL,
                'status': DisasterStatusChoices.ACTIVE,
                'affected_location': 'Moratuwa & Colombo South',
                'declared_at': ref_time - timedelta(hours=24),
            }
        )
        evt.status = DisasterStatusChoices.ACTIVE
        evt.save()
        disaster_event_id = evt.id

    req1 = ResourceRequest(
        id="EVAL-REQ-01",
        recipient=recipient_1, # type: ignore
        item_name="Prepared Cooked Meals",
        category=ResourceCategoryChoices.COOKED_MEALS,
        requested_quantity=70.0,
        fulfilled_quantity=0.0,
        unit="kg",
        priority=RequestPriorityChoices.URGENT,
        status=RequestStatusChoices.OPEN,
        people_impacted=140,
        urgency_deadline=ref_time + timedelta(hours=6),
        is_disaster_relief=is_disaster,
        disaster_event_id=disaster_event_id,
        created_at=ref_time - timedelta(hours=3),
    )

    req2 = ResourceRequest(
        id="EVAL-REQ-02",
        recipient=recipient_2, # type: ignore
        item_name="Bakery Provisions",
        category=ResourceCategoryChoices.BAKERY,
        requested_quantity=50.0,
        fulfilled_quantity=0.0,
        unit="kg",
        priority=RequestPriorityChoices.HIGH,
        status=RequestStatusChoices.OPEN,
        people_impacted=100,
        urgency_deadline=ref_time + timedelta(hours=12),
        is_disaster_relief=is_disaster,
        disaster_event_id=disaster_event_id,
        created_at=ref_time - timedelta(hours=2),
    )

    req3 = ResourceRequest(
        id="EVAL-REQ-03",
        recipient=recipient_3, # type: ignore
        item_name="Fresh Produce Packs",
        category=ResourceCategoryChoices.FRESH_PRODUCE,
        requested_quantity=80.0,
        fulfilled_quantity=0.0,
        unit="kg",
        priority=RequestPriorityChoices.MEDIUM,
        status=RequestStatusChoices.OPEN,
        people_impacted=160,
        urgency_deadline=ref_time + timedelta(hours=24),
        is_disaster_relief=is_disaster,
        disaster_event_id=disaster_event_id,
        created_at=ref_time - timedelta(hours=1),
    )

    requests = [req1, req2, req3]

    return resources, requests, ref_time
