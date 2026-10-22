import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRoleAssignment, RoleChoices
from apps.organizations.models import Organization, OrganizationTypeChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from apps.deliveries.models import Allocation, DeliveryTask, DeliveryTaskStatusChoices

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
def test_allocation_atomic_and_no_overallocation(client):
    coord = User.objects.create_user(email='c@test.lk', password='pw')
    UserRoleAssignment.objects.create(user=coord, role=RoleChoices.COORDINATOR, is_approved=True)

    org_provider = Organization.objects.create(name='Donor Org', type=OrganizationTypeChoices.BAKERY, verified=True, contact_email='d@test.lk', contact_phone='1', address='Moratuwa')
    org_recipient = Organization.objects.create(name='Shelter Org', type=OrganizationTypeChoices.SHELTER, verified=True, contact_email='s@test.lk', contact_phone='2', address='Moratuwa')

    now = timezone.now()
    resource = Resource.objects.create(
        provider=org_provider, name='Rice & Curry', category=ResourceCategoryChoices.COOKED_MEALS,
        quantity=30.0, pickup_start=now, pickup_end=now + timedelta(hours=4),
        safe_until=now + timedelta(hours=8), status=ResourceStatusChoices.AVAILABLE
    )

    req = ResourceRequest.objects.create(
        recipient=org_recipient, item_name='Lunch Meals', category=ResourceCategoryChoices.COOKED_MEALS,
        requested_quantity=50.0, urgency_deadline=now + timedelta(hours=4)
    )

    client.force_authenticate(user=coord)

    # 1. Over-allocation attempt: allocating 40 kg when only 30 kg is available
    over_resp = client.post('/api/v1/allocations/', {
        'resource': resource.id,
        'request': req.id,
        'allocatedQuantity': 40.0
    }, format='json')
    assert over_resp.status_code == 400
    assert 'exceeds available resource quantity' in str(over_resp.data)

    # 2. Valid allocation: 20 kg
    valid_resp = client.post('/api/v1/allocations/', {
        'resource': resource.id,
        'request': req.id,
        'allocatedQuantity': 20.0
    }, format='json')
    assert valid_resp.status_code == 201

    resource.refresh_from_db()
    req.refresh_from_db()
    assert resource.allocated_quantity == 20.0
    assert resource.available_quantity == 10.0
    assert req.fulfilled_quantity == 20.0
    assert req.status == RequestStatusChoices.PARTIALLY_ALLOCATED

    # Delivery task was automatically created in AVAILABLE state
    task = DeliveryTask.objects.get(allocation_id=valid_resp.data['id'])
    assert task.status == DeliveryTaskStatusChoices.AVAILABLE
    assert task.quantity == 20.0

@pytest.mark.django_db
def test_delivery_state_machine_lifecycle(client):
    vol_user = User.objects.create_user(email='v@test.lk', password='pw', full_name='Courier Dinesh')
    UserRoleAssignment.objects.create(user=vol_user, role=RoleChoices.VOLUNTEER, is_approved=True)
    volunteer = Volunteer.objects.create(user=vol_user, status=VolunteerAvailabilityChoices.AVAILABLE, verified=True)

    org_provider = Organization.objects.create(name='D Org', type=OrganizationTypeChoices.BAKERY, contact_email='d@test.lk', contact_phone='1', address='Moratuwa')
    org_recipient = Organization.objects.create(name='R Org', type=OrganizationTypeChoices.SHELTER, contact_email='r@test.lk', contact_phone='2', address='Moratuwa')

    now = timezone.now()
    res = Resource.objects.create(provider=org_provider, name='Bread', category=ResourceCategoryChoices.BAKERY, quantity=10.0, pickup_start=now, pickup_end=now+timedelta(hours=2))
    req = ResourceRequest.objects.create(recipient=org_recipient, item_name='Bread', category=ResourceCategoryChoices.BAKERY, requested_quantity=10.0, urgency_deadline=now+timedelta(hours=2))

    allocation = Allocation.objects.create(resource=res, request=req, allocated_quantity=10, status='APPROVED')
    task = DeliveryTask.objects.create(
        allocation=allocation, resource=res, request=req, title='Deliver Bread', cargo_description='10kg Bread',
        quantity=10.0, pickup_address=org_provider.address, delivery_address=org_recipient.address,
        delivery_deadline=now+timedelta(hours=2), status=DeliveryTaskStatusChoices.AVAILABLE
    )

    client.force_authenticate(user=vol_user)

    # Cannot jump directly from AVAILABLE to DELIVERED
    jump_resp = client.post(f'/api/v1/delivery-tasks/{task.id}/delivered/')
    assert jump_resp.status_code == 403  # An unassigned courier cannot mutate the task.

    # 1. Accept Task
    accept_resp = client.post(f'/api/v1/delivery-tasks/{task.id}/accept/')
    assert accept_resp.status_code == 200
    task.refresh_from_db()
    assert task.status == DeliveryTaskStatusChoices.ACCEPTED
    assert task.volunteer == volunteer

    # 2. Arrive at pickup
    arr_pick_resp = client.post(f'/api/v1/delivery-tasks/{task.id}/arrive_pickup/')
    assert arr_pick_resp.status_code == 200
    task.refresh_from_db()
    assert task.status == DeliveryTaskStatusChoices.ARRIVED_PICKUP

    # 3. Confirm picked up
    pick_resp = client.post(f'/api/v1/delivery-tasks/{task.id}/picked_up/')
    assert pick_resp.status_code == 200
    task.refresh_from_db()
    assert task.status == DeliveryTaskStatusChoices.PICKED_UP

    # 4. Arrive at delivery
    arr_del_resp = client.post(f'/api/v1/delivery-tasks/{task.id}/arrive_delivery/')
    assert arr_del_resp.status_code == 200
    task.refresh_from_db()
    assert task.status == DeliveryTaskStatusChoices.ARRIVED_DELIVERY

    # 5. Confirm delivered
    del_resp = client.post(f'/api/v1/delivery-tasks/{task.id}/delivered/')
    assert del_resp.status_code == 200
    task.refresh_from_db()
    assert task.status == DeliveryTaskStatusChoices.DELIVERED

    volunteer.refresh_from_db()
    assert volunteer.completed_deliveries_count == 1
    assert volunteer.status == VolunteerAvailabilityChoices.AVAILABLE
