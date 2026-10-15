import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient

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
from apps.intelligence.services.eligibility import evaluate_resource_request_eligibility, is_category_compatible
from apps.intelligence.services.baseline_matching import run_fcfs_baseline, run_nearest_baseline
from apps.intelligence.services.optimizer import solve_resource_allocation
from apps.intelligence.services.volunteer_assignment import match_volunteer_for_allocation
from apps.intelligence.services.disaster_priority import analyze_disaster_emergency_needs
from apps.intelligence.services.recovery import create_disruption_and_preview_recovery, apply_recovery_plan
from apps.intelligence.services.approval import approve_recommendation_batch, reject_recommendation_batch, apply_recommendation_batch

@pytest.fixture
def coordinator_user():
    user = User.objects.create_user(
        email='coord@dmc.test.lk',
        password='TestPassword123!',
        full_name='Test Coordinator'
    )
    UserRoleAssignment.objects.create(user=user, role=RoleChoices.COORDINATOR, is_approved=True)
    return user

@pytest.fixture
def regular_user():
    user = User.objects.create_user(
        email='volunteer@test.lk',
        password='TestPassword123!',
        full_name='Test Volunteer'
    )
    UserRoleAssignment.objects.create(user=user, role=RoleChoices.VOLUNTEER, is_approved=True)
    return user

@pytest.fixture
def test_setup():
    now = timezone.now()
    # Provider
    prov_org = Organization.objects.create(
        id='ORG-PROV-TEST',
        name='City Bakery Test',
        type=OrganizationTypeChoices.BAKERY,
        verified=True,
        latitude=6.7730,
        longitude=79.8816,
    )
    # Recipient
    rec_org = Organization.objects.create(
        id='ORG-REC-TEST',
        name='Shelter Hope Test',
        type=OrganizationTypeChoices.SHELTER,
        verified=True,
        latitude=6.7800,
        longitude=79.8850,
    )
    # Resource Lot
    res = Resource.objects.create(
        id='RES-TEST-001',
        provider=prov_org,
        name='Fresh Bread Packs',
        category=ResourceCategoryChoices.BAKERY,
        quantity=30.0,
        unit='kg',
        pickup_start=now - timedelta(hours=1),
        pickup_end=now + timedelta(hours=8),
        safe_until=now + timedelta(hours=24),
        storage_requirements=StorageRequirementChoices.AMBIENT,
        status=ResourceStatusChoices.AVAILABLE,
    )
    # Request
    req = ResourceRequest.objects.create(
        id='REQ-TEST-001',
        recipient=rec_org,
        item_name='Breakfast Bread',
        category=ResourceCategoryChoices.BAKERY,
        requested_quantity=20.0,
        unit='kg',
        priority=RequestPriorityChoices.HIGH,
        urgency_deadline=now + timedelta(hours=10),
        status=RequestStatusChoices.OPEN,
    )
    return {
        'provider': prov_org,
        'recipient': rec_org,
        'resource': res,
        'request': req,
    }

@pytest.mark.django_db
def test_hard_constraint_eligibility_success(test_setup):
    res = test_setup['resource']
    req = test_setup['request']

    result = evaluate_resource_request_eligibility(res, req)
    assert result.is_eligible is True
    assert len(result.reasons_rejected) == 0
    assert result.compatible_quantity == 20.0
    assert result.distance_km < 5.0

@pytest.mark.django_db
def test_hard_constraint_expired_food_rejection(test_setup):
    now = timezone.now()
    res = test_setup['resource']
    req = test_setup['request']

    # Mark expired in the past
    res.safe_until = now - timedelta(hours=2)
    res.save()

    result = evaluate_resource_request_eligibility(res, req)
    assert result.is_eligible is False
    assert any("expired" in r.lower() for r in result.reasons_rejected)

@pytest.mark.django_db
def test_hard_constraint_unverified_provider_rejection(test_setup):
    prov = test_setup['provider']
    prov.verified = False
    prov.save()

    res = test_setup['resource']
    req = test_setup['request']

    result = evaluate_resource_request_eligibility(res, req)
    assert result.is_eligible is False
    assert any("unverified" in r.lower() for r in result.reasons_rejected)

@pytest.mark.django_db
def test_hard_constraint_category_mismatch(test_setup):
    res = test_setup['resource']
    req = test_setup['request']

    req.category = ResourceCategoryChoices.DRINKING_WATER
    req.save()

    result = evaluate_resource_request_eligibility(res, req)
    assert result.is_eligible is False
    assert any("mismatch" in r.lower() for r in result.reasons_rejected)

@pytest.mark.django_db
def test_baselines_reproducibility_and_constraints(test_setup):
    res = test_setup['resource']
    req = test_setup['request']

    fcfs = run_fcfs_baseline([res], [req])
    assert fcfs.fulfilled_demand_pct == 100.0
    assert fcfs.total_allocated_quantity == 20.0
    assert fcfs.leftover_inventory == 10.0
    assert len(fcfs.allocations) == 1

    nearest = run_nearest_baseline([res], [req])
    assert nearest.fulfilled_demand_pct == 100.0
    assert nearest.total_allocated_quantity == 20.0
    assert nearest.leftover_inventory == 10.0

@pytest.mark.django_db
def test_ortools_optimizer_solution(test_setup):
    res = test_setup['resource']
    req = test_setup['request']

    plan = solve_resource_allocation([res], [req], time_limit_seconds=3.0)
    assert plan.solver_status in ('OPTIMAL', 'FEASIBLE')
    assert plan.fulfilled_demand_pct == 100.0
    assert plan.total_allocated_quantity == 20.0
    assert plan.leftover_inventory == 10.0
    assert len(plan.allocations) == 1
    assert plan.allocations[0]['allocated_quantity'] == 20.0

@pytest.mark.django_db
def test_volunteer_carrying_capacity_feasibility(test_setup):
    user_v = User.objects.create_user(email='driver@test.lk', password='P1', full_name='Kamal Driver')
    UserRoleAssignment.objects.create(user=user_v, role=RoleChoices.VOLUNTEER, is_approved=True)
    vol = Volunteer.objects.create(
        user=user_v,
        status=VolunteerAvailabilityChoices.AVAILABLE,
        vehicle_type=VehicleTypeChoices.MOTORCYCLE,
        vehicle_capacity_kg=15.0,  # 15 kg max
        verified=True,
        latitude=6.7730,
        longitude=79.8816,
    )

    res = test_setup['resource']
    req = test_setup['request']

    # Allocated quantity is 25 kg > 15 kg capacity -> Not feasible for this courier
    result_infeasible = match_volunteer_for_allocation(res, req, allocated_quantity=25.0)
    assert result_infeasible.is_feasible is False
    assert result_infeasible.volunteer is None

    # Allocated quantity is 10 kg <= 15 kg capacity -> Feasible
    result_feasible = match_volunteer_for_allocation(res, req, allocated_quantity=10.0)
    assert result_feasible.is_feasible is True
    assert result_feasible.volunteer.id == vol.id

@pytest.mark.django_db
def test_approval_and_atomic_apply_workflow(test_setup, coordinator_user):
    res = test_setup['resource']
    req = test_setup['request']

    # 1. Create a recommendation batch
    batch = RecommendationBatch.objects.create(
        mode=OperatingModeChoices.NORMAL,
        method=IntelligenceMethodChoices.ORTOOLS_CPSAT,
        status=RecommendationStatusChoices.PENDING_APPROVAL,
        created_by=coordinator_user,
        total_allocated_quantity=20.0,
    )
    rec = OptimizationRecommendation.objects.create(
        batch=batch,
        resource=res,
        request=req,
        allocated_quantity=20.0,
        unit=res.unit,
        explanation="Test explanation",
        suggested_action="Test action",
        status=RecommendationStatusChoices.PENDING_APPROVAL,
    )

    # 2. Coordinator approves
    approved_batch = approve_recommendation_batch(batch.id, coordinator_user)
    assert approved_batch.status == RecommendationStatusChoices.APPROVED

    # 3. Coordinator applies batch atomically
    result = apply_recommendation_batch(approved_batch.id, coordinator_user)
    assert result['success'] is True
    assert result['allocations_count'] == 1
    assert result['delivery_tasks_count'] == 1

    # Verify inventory was decremented and records committed
    res.refresh_from_db()
    req.refresh_from_db()
    assert res.allocated_quantity == 20.0
    assert res.available_quantity == 10.0
    assert req.fulfilled_quantity == 20.0
    assert req.status == RequestStatusChoices.ALLOCATED

    # Verify cannot re-apply applied batch (duplicate prevention)
    with pytest.raises(ValueError, match="already been APPLIED"):
        apply_recommendation_batch(approved_batch.id, coordinator_user)

@pytest.mark.django_db
def test_concurrent_inventory_conflict_rejection(test_setup, coordinator_user):
    res = test_setup['resource']
    req = test_setup['request']

    batch = RecommendationBatch.objects.create(
        status=RecommendationStatusChoices.APPROVED,
        approved_by=coordinator_user,
    )
    OptimizationRecommendation.objects.create(
        batch=batch,
        resource=res,
        request=req,
        allocated_quantity=20.0,
    )

    # Simulate external concurrent transaction allocating the resource first
    res.allocated_quantity = 25.0  # available becomes 5.0 kg < 20.0 kg
    res.save()

    # Applying the stale batch must raise conflict error and rollback
    with pytest.raises(ValueError, match="Concurrent inventory conflict"):
        apply_recommendation_batch(batch.id, coordinator_user)

@pytest.mark.django_db
def test_disruption_recovery_preview_and_apply(test_setup, coordinator_user):
    res = test_setup['resource']
    req = test_setup['request']

    alloc = Allocation.objects.create(
        resource=res,
        request=req,
        allocated_quantity=10.0,
    )
    task = DeliveryTask.objects.create(
        allocation=alloc,
        resource=res,
        request=req,
        title="Test Task",
        cargo_description="Bread",
        quantity=10.0,
        unit="kg",
        status=DeliveryTaskStatusChoices.ACCEPTED,
        pickup_address="A",
        delivery_address="B",
        delivery_deadline=timezone.now() + timedelta(hours=5),
    )

    # Report disruption
    preview = create_disruption_and_preview_recovery(
        task_id=task.id,
        event_type=DisruptionTypeChoices.ROAD_RESTRICTION,
        details="Route flooded near Moratuwa canal.",
        user=coordinator_user,
    )
    assert preview['disruption_id'] is not None
    assert preview['approval_required'] is True

    task.refresh_from_db()
    assert task.status == DeliveryTaskStatusChoices.DISRUPTED

    # Apply recovery
    result = apply_recovery_plan(preview['disruption_id'], coordinator_user)
    assert result['success'] is True

@pytest.mark.django_db
def test_intelligence_api_permissions(coordinator_user, regular_user):
    client = APIClient()

    # 1. Unauthenticated gets 401/403
    resp = client.get('/api/v1/intelligence/matches/')
    assert resp.status_code in (401, 403)

    # 2. Regular user cannot execute optimizer
    client.force_authenticate(user=regular_user)
    resp = client.post('/api/v1/intelligence/optimize/', {'method': 'ORTOOLS_CPSAT'}, format='json')
    assert resp.status_code == 403

    # 3. Coordinator can access matches and optimize
    client.force_authenticate(user=coordinator_user)
    resp = client.get('/api/v1/intelligence/matches/')
    assert resp.status_code == 200

    resp = client.get('/api/v1/intelligence/analytics/')
    assert resp.status_code == 200
    assert 'inventory_metrics' in resp.data
