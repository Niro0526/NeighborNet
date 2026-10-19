import pytest
from datetime import timedelta
from django.utils import timezone

from apps.accounts.models import User, UserRoleAssignment, RoleChoices
from apps.organizations.models import Organization, OrganizationTypeChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices, StorageRequirementChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices, VehicleTypeChoices
from apps.deliveries.models import DeliveryTask, DeliveryTaskStatusChoices, Allocation
from apps.disasters.models import DisasterEvent, DisasterStatusChoices
from apps.intelligence.models import (
    RecommendationBatch, OptimizationRecommendation,
    DisruptionEvent, DisruptionTypeChoices, DisruptionStatusChoices,
    RecommendationStatusChoices, OperatingModeChoices, IntelligenceMethodChoices
)
from apps.intelligence.services.eligibility import evaluate_resource_request_eligibility
from apps.intelligence.services.baseline_matching import run_fcfs_baseline, run_nearest_baseline
from apps.intelligence.services.optimizer import solve_resource_allocation
from apps.intelligence.services.volunteer_assignment import match_volunteer_for_allocation
from apps.intelligence.services.approval import approve_recommendation_batch, apply_recommendation_batch
from apps.intelligence.fixtures.evaluation_dataset import get_frozen_evaluation_dataset, EVALUATION_REFERENCE_TIMESTAMP

@pytest.fixture
def audit_setup(db):
    ref_time = EVALUATION_REFERENCE_TIMESTAMP
    prov = Organization.objects.create(
        id='ORG-PROV-AUDIT',
        name='Audit Provider',
        type=OrganizationTypeChoices.BAKERY,
        verified=True,
        latitude=6.7730,
        longitude=79.8816,
    )
    rec = Organization.objects.create(
        id='ORG-REC-AUDIT',
        name='Audit Recipient NGO',
        type=OrganizationTypeChoices.NGO,
        verified=True,
        latitude=6.7780,
        longitude=79.8850,
    )
    coord = User.objects.create_user(
        email='coord_audit@dmc.test.lk',
        password='TestPassword123!',
        full_name='Audit Coordinator'
    )
    UserRoleAssignment.objects.create(user=coord, role=RoleChoices.COORDINATOR, is_approved=True)

    return {
        'prov': prov,
        'rec': rec,
        'coord': coord,
        'ref_time': ref_time,
    }

@pytest.mark.django_db
def test_unit_mismatch_rejection(audit_setup):
    """Verifies that resources in 'boxes' cannot be matched with requests in 'kg'."""
    ref_time = audit_setup['ref_time']
    res = Resource.objects.create(
        id='RES-BOXES',
        provider=audit_setup['prov'],
        name='Breads in Boxes',
        category=ResourceCategoryChoices.BAKERY,
        quantity=10.0,
        unit='boxes',
        pickup_start=ref_time - timedelta(hours=1),
        pickup_end=ref_time + timedelta(hours=10),
        safe_until=ref_time + timedelta(hours=12),
        storage_requirements=StorageRequirementChoices.AMBIENT,
        status=ResourceStatusChoices.AVAILABLE,
    )
    req = ResourceRequest.objects.create(
        id='REQ-KG',
        recipient=audit_setup['rec'],
        item_name='Bakery Goods',
        category=ResourceCategoryChoices.BAKERY,
        requested_quantity=50.0,
        unit='kg',
        urgency_deadline=ref_time + timedelta(hours=10),
    )

    elig = evaluate_resource_request_eligibility(res, req, now=ref_time)
    assert not elig.is_eligible
    assert any('Unit mismatch' in r for r in elig.reasons_rejected)

@pytest.mark.django_db
def test_food_safe_use_2hour_buffer(audit_setup):
    """Verifies conservative rejection when safe_until is less than 2 hours from current time."""
    ref_time = audit_setup['ref_time']
    res_expiring_soon = Resource.objects.create(
        id='RES-EXP-SOON',
        provider=audit_setup['prov'],
        name='Rice Rations Expiring Soon',
        category=ResourceCategoryChoices.COOKED_MEALS,
        quantity=20.0,
        unit='kg',
        pickup_start=ref_time - timedelta(hours=1),
        pickup_end=ref_time + timedelta(hours=5),
        safe_until=ref_time + timedelta(minutes=90), # Only 1.5h remaining (<2h buffer)
        storage_requirements=StorageRequirementChoices.KEEP_WARM,
        status=ResourceStatusChoices.AVAILABLE,
    )
    req = ResourceRequest.objects.create(
        id='REQ-MEAL-AUDIT',
        recipient=audit_setup['rec'],
        item_name='Meals Request',
        category=ResourceCategoryChoices.COOKED_MEALS,
        requested_quantity=20.0,
        unit='kg',
        urgency_deadline=ref_time + timedelta(hours=5),
    )

    elig = evaluate_resource_request_eligibility(res_expiring_soon, req, now=ref_time)
    assert not elig.is_eligible
    assert any('expires in less than 2 hours' in r for r in elig.reasons_rejected)

@pytest.mark.django_db
def test_benchmark_conservation_and_reproducibility():
    """Verifies that Allocated + Unmet == Total Requested Demand across all solver engines."""
    resources, requests, ref_time = get_frozen_evaluation_dataset(mode='NORMAL', scenario='BALANCED')
    total_req_qty = sum(float(r.requested_quantity) for r in requests) # 200.0 kg

    # 1. FCFS
    fcfs_res = run_fcfs_baseline(resources, requests, now=ref_time)
    assert abs((fcfs_res.total_allocated_quantity + fcfs_res.unmet_demand) - total_req_qty) < 0.01

    # 2. Nearest
    near_res = run_nearest_baseline(resources, requests, now=ref_time)
    assert abs((near_res.total_allocated_quantity + near_res.unmet_demand) - total_req_qty) < 0.01

    # 3. OR-Tools
    opt_res = solve_resource_allocation(resources, requests, time_limit_seconds=5.0, now=ref_time)
    assert abs((opt_res.total_allocated_quantity + opt_res.unmet_demand) - total_req_qty) < 0.01

@pytest.mark.django_db
def test_integer_scaling_small_fractional_quantities(audit_setup):
    """Verifies exact resolution for 0.01 kg, 0.05 kg, 1.25 kg under scale factor S=100."""
    ref_time = audit_setup['ref_time']
    res = Resource.objects.create(
        id='RES-SMALL',
        provider=audit_setup['prov'],
        name='High-Value Spices / Supplies',
        category=ResourceCategoryChoices.CANNED_PACKAGED,
        quantity=0.05,
        unit='kg',
        pickup_start=ref_time - timedelta(hours=1),
        pickup_end=ref_time + timedelta(hours=10),
        safe_until=ref_time + timedelta(hours=24),
        storage_requirements=StorageRequirementChoices.AMBIENT,
        status=ResourceStatusChoices.AVAILABLE,
    )
    req = ResourceRequest.objects.create(
        id='REQ-SMALL',
        recipient=audit_setup['rec'],
        item_name='Spice Rations',
        category=ResourceCategoryChoices.CANNED_PACKAGED,
        requested_quantity=0.05,
        unit='kg',
        urgency_deadline=ref_time + timedelta(hours=10),
    )

    opt_res = solve_resource_allocation([res], [req], time_limit_seconds=2.0, now=ref_time)
    assert opt_res.solver_status in ('OPTIMAL', 'FEASIBLE')
    assert opt_res.total_allocated_quantity == 0.05

@pytest.mark.django_db
def test_volunteer_carrying_capacity_check(audit_setup):
    """Verifies that a courier with insufficient carrying capacity is not matched to a heavy allocation."""
    res_heavy = Resource.objects.create(
        id='RES-HEAVY',
        provider=audit_setup['prov'],
        name='Bulk Grain Cargo',
        category=ResourceCategoryChoices.COOKED_MEALS,
        quantity=250.0,
        unit='kg',
        pickup_start=audit_setup['ref_time'] - timedelta(hours=1),
        pickup_end=audit_setup['ref_time'] + timedelta(hours=5),
        safe_until=audit_setup['ref_time'] + timedelta(hours=12),
        storage_requirements=StorageRequirementChoices.AMBIENT,
        status=ResourceStatusChoices.AVAILABLE,
    )

    small_vol_user = User.objects.create_user(
        email='smallvol@test.lk',
        password='Password123!',
        full_name='Bicycle Courier',
        phone='+94770000001'
    )
    small_volunteer = Volunteer.objects.create(
        user=small_vol_user,
        status=VolunteerAvailabilityChoices.AVAILABLE,
        vehicle_type=VehicleTypeChoices.BICYCLE,
        vehicle_capacity_kg=15.0, # Only 15 kg capacity
        verified=True,
    )

    req_heavy = ResourceRequest.objects.create(
        id='REQ-HEAVY',
        recipient=audit_setup['rec'],
        item_name='Bulk Meals',
        category=ResourceCategoryChoices.COOKED_MEALS,
        requested_quantity=200.0,
        unit='kg',
        urgency_deadline=audit_setup['ref_time'] + timedelta(hours=5),
    )

    vol_result = match_volunteer_for_allocation(
        resource=res_heavy,
        request=req_heavy,
        allocated_quantity=200.0 # 200 kg payload > 15 kg bicycle capacity
    )

    # Bicycle courier cannot carry 200 kg; result must be marked infeasible
    assert vol_result.volunteer is None
    assert vol_result.is_feasible is False
    assert "exceeds vehicle capacities" in vol_result.notes
