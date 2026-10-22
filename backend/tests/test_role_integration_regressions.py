import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRoleAssignment
from apps.organizations.models import Organization, OrganizationMembership
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from apps.deliveries.models import Allocation, DeliveryTask
from apps.volunteers.models import Volunteer
from apps.notifications.models import Notification
from apps.notifications.services import send_notification

@pytest.fixture
def flow(db):
    users = {}
    for role in ['FOOD_PROVIDER', 'RECIPIENT', 'COORDINATOR', 'VOLUNTEER']:
        user = User.objects.create_user(email=f'{role}@audit.test', password='test')
        UserRoleAssignment.objects.create(user=user, role=role, is_approved=True)
        users[role] = user
    provider = Organization.objects.create(name='Provider', type='BAKERY', verified=True)
    recipient = Organization.objects.create(name='NGO', type='NGO', verified=True)
    OrganizationMembership.objects.create(organization=provider, user=users['FOOD_PROVIDER'])
    OrganizationMembership.objects.create(organization=recipient, user=users['RECIPIENT'])
    now = timezone.now()
    resource = Resource.objects.create(provider=provider, name='Bread', category='bakery', quantity=20, unit='kg', pickup_start=now, pickup_end=now+timedelta(hours=2), safe_until=now+timedelta(hours=5))
    req = ResourceRequest.objects.create(recipient=recipient, item_name='Bread', category='bakery', requested_quantity=20, unit='kg', urgency_deadline=now+timedelta(hours=4))
    volunteer = Volunteer.objects.create(user=users['VOLUNTEER'], verified=True, status='available', vehicle_capacity_kg=25)
    return users, resource, req, volunteer

@pytest.mark.django_db
def test_pending_approval_and_assigned_courier_only(flow):
    users, resource, req, volunteer = flow
    client = APIClient()
    client.force_authenticate(users['RECIPIENT'])
    response = client.post('/api/v1/allocations/', {'resource':resource.pk, 'request':req.pk, 'allocatedQuantity':10}, format='json')
    assert response.status_code == 201
    allocation = Allocation.objects.get(pk=response.data['id'])
    task = allocation.delivery_task
    assert allocation.status == 'PENDING'
    client.force_authenticate(users['VOLUNTEER'])
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/accept/').status_code in [403,404]
    assert not DeliveryTask.objects.filter(pk=task.pk, status='ACCEPTED').exists()
    client.force_authenticate(users['COORDINATOR'])
    assert client.post(f'/api/v1/allocations/{allocation.pk}/approve/').status_code == 200
    client.force_authenticate(users['VOLUNTEER'])
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/accept/').status_code == 200
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/complete/').status_code == 400
    client.force_authenticate(users['FOOD_PROVIDER'])
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/arrived_delivery/').status_code == 403
    assert client.patch(f'/api/v1/delivery-tasks/{task.pk}/', {'status':'DELIVERED'}, format='json').status_code == 405
    client.force_authenticate(users['VOLUNTEER'])
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/arrived_pickup/').status_code == 200
    client.force_authenticate(users['FOOD_PROVIDER'])
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/pickup/').status_code == 200
    resource.refresh_from_db()
    assert resource.status == 'AVAILABLE' and resource.available_quantity == 10
    client.force_authenticate(users['VOLUNTEER'])
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/arrived_delivery/').status_code == 200
    client.force_authenticate(users['RECIPIENT'])
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/complete/').status_code == 200
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/complete/').status_code == 400
    req.refresh_from_db()
    volunteer.refresh_from_db()
    assert req.status == 'PARTIALLY_ALLOCATED'  # One partial delivery cannot fulfill all demand.
    assert volunteer.completed_deliveries_count == 1

@pytest.mark.django_db
def test_cross_organization_and_role_mutations_denied(flow):
    users, resource, req, _ = flow
    client = APIClient()
    client.force_authenticate(users['VOLUNTEER'])
    assert client.post('/api/v1/resources/', {}, format='json').status_code == 403
    assert client.post('/api/v1/resource-requests/', {}, format='json').status_code == 403
    assert client.post('/api/v1/allocations/', {'resource':resource.pk,'request':req.pk,'allocatedQuantity':1}, format='json').status_code == 403
    client.force_authenticate(users['RECIPIENT'])
    assert client.patch(f'/api/v1/resources/{resource.pk}/', {'quantity':99}, format='json').status_code == 403
    client.force_authenticate(users['FOOD_PROVIDER'])
    assert client.patch(f'/api/v1/organizations/{req.recipient_id}/', {'name':'Forged'}, format='json').status_code == 403

@pytest.mark.django_db
def test_notification_broadcast_has_independent_read_state(flow):
    users, _, _, _ = flow
    other = User.objects.create_user(email='other@audit.test', password='test')
    UserRoleAssignment.objects.create(user=other, role='VOLUNTEER', is_approved=True)
    send_notification('Audit broadcast', 'Test', role_target='VOLUNTEER', event_key='audit-broadcast')
    client = APIClient()
    client.force_authenticate(users['VOLUNTEER'])
    mine = Notification.objects.get(user=users['VOLUNTEER'], title='Audit broadcast')
    theirs = Notification.objects.get(user=other, title='Audit broadcast')
    assert client.post(f'/api/v1/notifications/{mine.pk}/mark_read/').status_code == 200
    assert client.post(f'/api/v1/notifications/{theirs.pk}/mark_read/').status_code == 404
    theirs.refresh_from_db()
    assert not theirs.read
