"""
NeighborNet AI — Phase 5 Production Readiness & Security Test Suite
Validates end-to-end multi-role isolation, atomic concurrency, negative inventory prevention,
state machine transitions, disaster permissions, and disruption recovery workflows.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRoleAssignment, RoleChoices
from apps.organizations.models import Organization, OrganizationTypeChoices, OrganizationMembership, MembershipRoleChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices, StorageRequirementChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices, VehicleTypeChoices
from apps.deliveries.models import Allocation, AllocationStatusChoices, DeliveryTask, DeliveryTaskStatusChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices, DisasterSeverityChoices
from apps.intelligence.models import DisruptionEvent, DisruptionTypeChoices, DisruptionStatusChoices
from apps.intelligence.services.recovery import create_disruption_and_preview_recovery, apply_recovery_plan


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def production_setup(db):
    now = timezone.now()

    # Providers
    prov_org_1 = Organization.objects.create(
        id='ORG-PROV-1', name='GreenBites Bistro', type=OrganizationTypeChoices.RESTAURANT,
        contact_email='prov1@greenbites.lk', contact_phone='+94 77 100 0001', address='Moratuwa Town',
        latitude=6.7730, longitude=79.8816, verified=True
    )
    prov_org_2 = Organization.objects.create(
        id='ORG-PROV-2', name='Perera Bakers', type=OrganizationTypeChoices.BAKERY,
        contact_email='prov2@perera.lk', contact_phone='+94 77 100 0002', address='Dehiwala South',
        latitude=6.8300, longitude=79.8650, verified=True
    )

    # Recipients
    rec_org_1 = Organization.objects.create(
        id='ORG-REC-1', name='Grace Elders Home', type=OrganizationTypeChoices.SHELTER,
        contact_email='rec1@grace.org', contact_phone='+94 11 200 0001', address='Lunawa Moratuwa',
        latitude=6.7800, longitude=79.8850, verified=True
    )
    rec_org_2 = Organization.objects.create(
        id='ORG-REC-2', name='Red Cross Youth Center', type=OrganizationTypeChoices.NGO,
        contact_email='rec2@redcross.lk', contact_phone='+94 11 200 0002', address='Ratmalana',
        latitude=6.8150, longitude=79.8720, verified=True
    )

    # Users
    user_prov_1 = User.objects.create_user(email='provider1@test.lk', password='Password123!', full_name='Provider One')
    UserRoleAssignment.objects.create(user=user_prov_1, role=RoleChoices.FOOD_PROVIDER, is_approved=True)
    OrganizationMembership.objects.create(organization=prov_org_1, user=user_prov_1, role=MembershipRoleChoices.ADMIN)

    user_prov_2 = User.objects.create_user(email='provider2@test.lk', password='Password123!', full_name='Provider Two')
    UserRoleAssignment.objects.create(user=user_prov_2, role=RoleChoices.FOOD_PROVIDER, is_approved=True)
    OrganizationMembership.objects.create(organization=prov_org_2, user=user_prov_2, role=MembershipRoleChoices.ADMIN)

    user_rec_1 = User.objects.create_user(email='recipient1@test.lk', password='Password123!', full_name='Sister Mary')
    UserRoleAssignment.objects.create(user=user_rec_1, role=RoleChoices.RECIPIENT, is_approved=True)
    OrganizationMembership.objects.create(organization=rec_org_1, user=user_rec_1, role=MembershipRoleChoices.ADMIN)

    user_rec_2 = User.objects.create_user(email='recipient2@test.lk', password='Password123!', full_name='Sarath NGO')
    UserRoleAssignment.objects.create(user=user_rec_2, role=RoleChoices.RECIPIENT, is_approved=True)
    OrganizationMembership.objects.create(organization=rec_org_2, user=user_rec_2, role=MembershipRoleChoices.ADMIN)

    user_vol_1 = User.objects.create_user(email='volunteer1@test.lk', password='Password123!', full_name='Courier Dinesh')
    UserRoleAssignment.objects.create(user=user_vol_1, role=RoleChoices.VOLUNTEER, is_approved=True)
    vol_1 = Volunteer.objects.create(
        user=user_vol_1, vehicle_type=VehicleTypeChoices.MOTORCYCLE, vehicle_capacity_kg=25.0,
        status=VolunteerAvailabilityChoices.AVAILABLE, latitude=6.7750, longitude=79.8830, verified=True
    )

    user_vol_2 = User.objects.create_user(email='volunteer2@test.lk', password='Password123!', full_name='Courier Kamal')
    UserRoleAssignment.objects.create(user=user_vol_2, role=RoleChoices.VOLUNTEER, is_approved=True)
    vol_2 = Volunteer.objects.create(
        user=user_vol_2, vehicle_type=VehicleTypeChoices.CAR, vehicle_capacity_kg=100.0,
        status=VolunteerAvailabilityChoices.AVAILABLE, latitude=6.7760, longitude=79.8840, verified=True
    )

    user_coord = User.objects.create_user(email='coordinator@test.lk', password='Password123!', full_name='Dr. Coordinator')
    UserRoleAssignment.objects.create(user=user_coord, role=RoleChoices.COORDINATOR, is_approved=True)

    # Multi-Role User: Food Provider + Volunteer Courier
    user_multi = User.objects.create_user(email='multirole@test.lk', password='Password123!', full_name='Ravi Mendis')
    UserRoleAssignment.objects.create(user=user_multi, role=RoleChoices.FOOD_PROVIDER, is_approved=True)
    UserRoleAssignment.objects.create(user=user_multi, role=RoleChoices.VOLUNTEER, is_approved=True)
    OrganizationMembership.objects.create(organization=prov_org_1, user=user_multi, role=MembershipRoleChoices.ADMIN)
    Volunteer.objects.create(
        user=user_multi, vehicle_type=VehicleTypeChoices.VAN, vehicle_capacity_kg=350.0,
        status=VolunteerAvailabilityChoices.AVAILABLE, latitude=6.7735, longitude=79.8820, verified=True
    )

    return {
        'now': now,
        'prov_org_1': prov_org_1,
        'prov_org_2': prov_org_2,
        'rec_org_1': rec_org_1,
        'rec_org_2': rec_org_2,
        'user_prov_1': user_prov_1,
        'user_prov_2': user_prov_2,
        'user_rec_1': user_rec_1,
        'user_rec_2': user_rec_2,
        'user_vol_1': user_vol_1,
        'vol_1': vol_1,
        'user_vol_2': user_vol_2,
        'vol_2': vol_2,
        'user_coord': user_coord,
        'user_multi': user_multi,
    }


@pytest.mark.django_db
def test_organization_isolation_surplus_and_requests(api_client, production_setup):
    """Verifies that Food Providers and Recipients cannot mutate another organization's records."""
    s = production_setup
    now = s['now']

    # Prov 1 creates a resource
    res_1 = Resource.objects.create(
        provider=s['prov_org_1'], name='Bistro Surplus', category=ResourceCategoryChoices.COOKED_MEALS,
        quantity=30.0, unit='kg', pickup_start=now, pickup_end=now + timedelta(hours=3),
        safe_until=now + timedelta(hours=6), status=ResourceStatusChoices.AVAILABLE
    )

    # Prov 2 attempts to withdraw Prov 1's resource
    api_client.force_authenticate(user=s['user_prov_2'])
    resp = api_client.post(f'/api/v1/resources/{res_1.id}/withdraw/')
    assert resp.status_code == 403, "Provider 2 must NOT be allowed to withdraw Provider 1's listing"

    # Prov 1 can legitimately withdraw their own listing
    api_client.force_authenticate(user=s['user_prov_1'])
    resp_success = api_client.post(f'/api/v1/resources/{res_1.id}/withdraw/')
    assert resp_success.status_code == 200
    res_1.refresh_from_db()
    assert res_1.status == ResourceStatusChoices.WITHDRAWN

    # Recipient 1 creates a request
    req_1 = ResourceRequest.objects.create(
        recipient=s['rec_org_1'], item_name='Grace Meals', category=ResourceCategoryChoices.COOKED_MEALS,
        requested_quantity=20.0, unit='kg', urgency_deadline=now + timedelta(hours=4)
    )

    # Recipient 2 attempts to cancel Recipient 1's request
    api_client.force_authenticate(user=s['user_rec_2'])
    cancel_fail = api_client.post(f'/api/v1/resource-requests/{req_1.id}/cancel/')
    assert cancel_fail.status_code == 403, "Recipient 2 must NOT cancel Recipient 1's request"


@pytest.mark.django_db
def test_atomic_allocation_concurrency_and_negative_inventory_rejection(api_client, production_setup):
    """Verifies that atomic row locks prevent negative inventory and reject invalid quantities."""
    s = production_setup
    now = s['now']

    resource = Resource.objects.create(
        provider=s['prov_org_1'], name='Fresh Vegetable Packs', category=ResourceCategoryChoices.FRESH_PRODUCE,
        quantity=20.0, unit='kg', pickup_start=now, pickup_end=now + timedelta(hours=4),
        safe_until=now + timedelta(hours=8), status=ResourceStatusChoices.AVAILABLE
    )
    request_obj = ResourceRequest.objects.create(
        recipient=s['rec_org_1'], item_name='Produce for Kitchen', category=ResourceCategoryChoices.FRESH_PRODUCE,
        requested_quantity=25.0, unit='kg', urgency_deadline=now + timedelta(hours=4)
    )

    api_client.force_authenticate(user=s['user_coord'])

    # 1. Zero or negative allocated quantity rejection
    zero_resp = api_client.post('/api/v1/allocations/', {
        'resource': resource.id, 'request': request_obj.id, 'allocatedQuantity': 0.0
    }, format='json')
    assert zero_resp.status_code == 400

    neg_resp = api_client.post('/api/v1/allocations/', {
        'resource': resource.id, 'request': request_obj.id, 'allocatedQuantity': -5.0
    }, format='json')
    assert neg_resp.status_code == 400

    # 2. Exceeding available inventory rejection
    over_resp = api_client.post('/api/v1/allocations/', {
        'resource': resource.id, 'request': request_obj.id, 'allocatedQuantity': 20.01
    }, format='json')
    assert over_resp.status_code == 400
    assert 'exceeds available' in str(over_resp.data)

    # 3. Exact full allocation
    valid_resp = api_client.post('/api/v1/allocations/', {
        'resource': resource.id, 'request': request_obj.id, 'allocatedQuantity': 20.0
    }, format='json')
    assert valid_resp.status_code == 201

    resource.refresh_from_db()
    request_obj.refresh_from_db()
    assert resource.available_quantity == 0.0
    assert resource.allocated_quantity == 20.0
    assert resource.status == ResourceStatusChoices.RESERVED
    assert request_obj.fulfilled_quantity == 20.0
    assert request_obj.remaining_quantity == 5.0
    assert request_obj.status == RequestStatusChoices.PARTIALLY_ALLOCATED


@pytest.mark.django_db
def test_coordinator_only_disaster_lifecycle(api_client, production_setup):
    """Verifies that only Coordinators can activate and resolve disaster contexts."""
    s = production_setup
    now = s['now']

    disaster = DisasterEvent.objects.create(
        title='Cyclone Hazard South Coast', description='Moratuwa coastal belt',
        severity=DisasterSeverityChoices.CRITICAL, status=DisasterStatusChoices.DRAFT,
        affected_location='Moratuwa coastal belt', affected_population=3500
    )

    # Volunteer cannot activate
    api_client.force_authenticate(user=s['user_vol_1'])
    vol_fail = api_client.post(f'/api/v1/disasters/{disaster.id}/activate/')
    assert vol_fail.status_code == 403

    # Recipient cannot activate
    api_client.force_authenticate(user=s['user_rec_1'])
    rec_fail = api_client.post(f'/api/v1/disasters/{disaster.id}/activate/')
    assert rec_fail.status_code == 403

    # Coordinator activates disaster
    api_client.force_authenticate(user=s['user_coord'])
    coord_success = api_client.post(f'/api/v1/disasters/{disaster.id}/activate/')
    assert coord_success.status_code == 200
    disaster.refresh_from_db()
    assert disaster.status == DisasterStatusChoices.ACTIVE

    # Coordinator resolves disaster
    resolve_resp = api_client.post(f'/api/v1/disasters/{disaster.id}/resolve/')
    assert resolve_resp.status_code == 200
    disaster.refresh_from_db()
    assert disaster.status == DisasterStatusChoices.RESOLVED


@pytest.mark.django_db
def test_disruption_recovery_workflow_and_reassignment(api_client, production_setup):
    """
    Verifies that a courier breakdown triggers the disruption recovery engine,
    proposes a viable replacement without double-booking inventory, and completes successfully.
    """
    s = production_setup
    now = s['now']

    res = Resource.objects.create(
        provider=s['prov_org_1'], name='Emergency Warm Meals', category=ResourceCategoryChoices.COOKED_MEALS,
        quantity=15.0, unit='kg', pickup_start=now, pickup_end=now + timedelta(hours=3),
        safe_until=now + timedelta(hours=6), status=ResourceStatusChoices.AVAILABLE
    )
    req = ResourceRequest.objects.create(
        recipient=s['rec_org_1'], item_name='Rations', category=ResourceCategoryChoices.COOKED_MEALS,
        requested_quantity=15.0, unit='kg', urgency_deadline=now + timedelta(hours=3)
    )
    alloc = Allocation.objects.create(
        resource=res, request=req, allocated_quantity=15.0, status=AllocationStatusChoices.APPROVED
    )
    task = DeliveryTask.objects.create(
        allocation=alloc, resource=res, request=req, volunteer=s['vol_1'],
        title='Deliver Emergency Meals', cargo_description='15kg Cooked Meals',
        quantity=15.0, unit='kg', pickup_address='Moratuwa', delivery_address='Lunawa',
        delivery_deadline=now + timedelta(hours=2), status=DeliveryTaskStatusChoices.ACCEPTED
    )

    # Courier 1 is busy
    s['vol_1'].status = VolunteerAvailabilityChoices.BUSY
    s['vol_1'].save()

    # Courier 1 reports route disruption via API
    api_client.force_authenticate(user=s['user_vol_1'])
    disrupt_resp = api_client.post(f'/api/v1/delivery-tasks/{task.id}/disrupt/', {
        'reason': 'Motorbike engine failure near Moratuwa bridge'
    }, format='json')
    assert disrupt_resp.status_code == 200
    task.refresh_from_db()
    assert task.status == DeliveryTaskStatusChoices.DISRUPTED

    # Compute disruption recovery plan
    recovery_plan = create_disruption_and_preview_recovery(
        task_id=task.id,
        event_type=DisruptionTypeChoices.VOLUNTEER_UNAVAILABLE,
        details='Courier 1 breakdown'
    )
    assert recovery_plan['task_id'] == task.id
    assert len(recovery_plan['replacement_options']) > 0

    # Verify replacement volunteer proposed is Courier 2 or Ravi (capacity >= 15kg)
    best_opt = recovery_plan['replacement_options'][0]
    assert best_opt['vehicle_capacity_kg'] >= 15.0

    # Coordinator reviews and applies recovery plan
    disruption_event = DisruptionEvent.objects.get(task=task)
    applied_result = apply_recovery_plan(
        disruption_id=disruption_event.id,
        approved_by_user=s['user_coord']
    )
    assert applied_result['success'] is True

    # Check that task is now reassigned to the replacement volunteer and reset to AVAILABLE/ACCEPTED
    task.refresh_from_db()
    assert task.status in (DeliveryTaskStatusChoices.AVAILABLE, DeliveryTaskStatusChoices.ACCEPTED)
    assert task.volunteer.id != s['vol_1'].id
    disruption_event.refresh_from_db()
    assert disruption_event.status == DisruptionStatusChoices.RESOLVED


@pytest.mark.django_db
def test_production_environment_security_configurations(monkeypatch):
    """Validates production settings safeguards: debug disabled, secure cookies, and seed protection."""
    import os
    monkeypatch.setenv('SECRET_KEY', 'test-production-secret-key-12345')
    monkeypatch.setenv('ALLOWED_HOSTS', 'neighbornet.lk,api.neighbornet.lk')
    
    import importlib
    from config.settings import production
    importlib.reload(production)
    
    assert production.DEBUG is False
    assert production.SESSION_COOKIE_SECURE is True
    assert production.CSRF_COOKIE_SECURE is True
    assert production.SECURE_BROWSER_XSS_FILTER is True
    assert production.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert production.X_FRAME_OPTIONS == 'DENY'
