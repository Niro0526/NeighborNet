from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import pytest
from django.db import connection, connections
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.requests.models import FoodClaim, PersonalLocation
from apps.notifications.models import Notification
from .test_role_integration_regressions import flow

BASE = '/api/v1/community-food/'


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def personal(email='individual@claims.test'):
    user = User.objects.create_user(email=email, password='Personal-test-843!')
    PersonalLocation.objects.create(user=user, address='Private home', latitude=6.773, longitude=79.8816)
    return user


def claim(client, resource, quantity=2, method='delivery'):
    return client.post(BASE, {'resource': resource.pk, 'quantity': quantity, 'method': method, 'safetyAcknowledged': True}, format='json')


def step(client, claim_id, status, **extra):
    return client.post(f'{BASE}{claim_id}/transition/', {'status': status, 'safetyAcknowledged': True, **extra}, format='json')


@pytest.mark.django_db
def test_real_registration_location_and_session_csrf():
    assert connection.vendor == 'postgresql', 'Run this flow against PostgreSQL, not SQLite.'
    client = APIClient(enforce_csrf_checks=True)
    response = client.post('/api/v1/auth/register/', {'email': 'new-person@claims.test', 'password': 'Personal-test-843!', 'full_name': 'Individual'}, format='json')
    assert response.status_code == 201, response.data
    user = User.objects.get(email='new-person@claims.test')
    assert user.get_approved_roles() == [] and not user.organization_memberships.exists()
    assert client.get(BASE+'offers/').status_code == 200
    payload = {'address': 'My home', 'latitude': 6.773, 'longitude': 79.8816}
    assert client.put(BASE+'location/', payload, format='json').status_code == 403
    token = client.get('/api/v1/auth/csrf/').data['csrfToken']
    assert client.put(BASE+'location/', payload, format='json', HTTP_X_CSRFTOKEN=token).status_code == 200
    assert PersonalLocation.objects.get(user=user).address == 'My home'
    assert client.put(BASE+'location/', {**payload, 'latitude': 91}, format='json', HTTP_X_CSRFTOKEN=token).status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('method', ['pickup', 'delivery'])
def test_complete_individual_flow_without_ngo(flow, method):
    users, resource, _, volunteer = flow
    recipient = personal()
    client = client_for(recipient)
    assert any(o['id'] == resource.pk for o in client.get(BASE+'offers/').data)
    response = claim(client, resource, method=method)
    assert response.status_code == 201, response.data
    claim_id = response.data['id']
    resource.refresh_from_db()
    assert resource.allocated_quantity == 2
    assert claim(client, resource).status_code == 409
    for user in [recipient, users['FOOD_PROVIDER'], users['COORDINATOR']]:
        assert Notification.objects.filter(user=user, event_key__contains=str(claim_id)).exists()
    assert step(client, claim_id, 'APPROVED').status_code == 403
    assert step(client_for(users['VOLUNTEER']), claim_id, 'ASSIGNED').status_code == 404
    coordinator = client_for(users['COORDINATOR'])
    assert step(coordinator, claim_id, 'APPROVED').status_code == 200
    provider = client_for(users['FOOD_PROVIDER'])
    data = provider.get(f'{BASE}{claim_id}/').data
    assert 'address' not in data and data['recipientName'] == 'Community recipient'
    assert client_for(personal('stranger@claims.test')).get(f'{BASE}{claim_id}/').status_code == 404
    if method == 'delivery':
        courier = client_for(users['VOLUNTEER'])
        assert 'address' not in courier.get(f'{BASE}{claim_id}/').data
        assert step(courier, claim_id, 'ASSIGNED').status_code == 200
        assert courier.get(f'{BASE}{claim_id}/').data['address'] == 'Private home'
        volunteer.refresh_from_db()
        assert volunteer.status == 'busy'
        assert step(courier, claim_id, 'DELIVERED').status_code == 403
    assert step(client, claim_id, 'PICKED_UP').status_code == 403
    code = {}
    if method == 'pickup':
        assert provider.get(f'{BASE}{claim_id}/').data['pickupCode'] is None
        assert step(provider, claim_id, 'PICKED_UP', pickupCode='wrong').status_code == 400
        code = {'pickupCode': client.get(f'{BASE}{claim_id}/').data['pickupCode']}
    assert step(provider, claim_id, 'PICKED_UP', **code).status_code == 200
    assert step(provider, claim_id, 'PICKED_UP').status_code == 403
    if method == 'delivery':
        assert step(courier, claim_id, 'DELIVERED').status_code == 200
        volunteer.refresh_from_db()
        assert volunteer.status == 'available' and volunteer.completed_deliveries_count == 1
    assert step(client, claim_id, 'RECEIVED').status_code == 200
    assert step(client, claim_id, 'RECEIVED').status_code == 403
    record = FoodClaim.objects.get(pk=claim_id)
    assert record.status == 'RECEIVED' and record.approved_by == users['COORDINATOR']
    expected = ['PENDING', 'APPROVED', 'ASSIGNED', 'PICKED_UP', 'DELIVERED', 'RECEIVED'] if method == 'delivery' else ['PENDING', 'APPROVED', 'PICKED_UP', 'RECEIVED']
    assert list(record.events.values_list('status', flat=True)) == expected
    assert provider.get(f'{BASE}{claim_id}/').data['status'] == 'RECEIVED'


@pytest.mark.django_db
def test_eligibility_availability_and_inventory_release(flow):
    users, resource, _, _ = flow
    user = personal()
    client = client_for(user)
    for quantity in [0, -1, 'NaN', 'Infinity', '1.001', 21]:
        assert claim(client, resource, quantity).status_code == 400
    response = claim(client, resource, 20)
    assert response.status_code == 201
    cid = response.data['id']
    resource.refresh_from_db()
    assert resource.status == 'RESERVED'
    assert step(client, cid, 'CANCELLED').status_code == 200
    resource.refresh_from_db()
    assert resource.available_quantity == 20 and resource.status == 'AVAILABLE'
    assert step(client, cid, 'CANCELLED').status_code == 403
    cid = claim(client, resource).data['id']
    resource.safe_until = timezone.now()+timedelta(minutes=30)
    resource.save()
    assert step(client_for(users['COORDINATOR']), cid, 'APPROVED').status_code == 400
    assert step(client_for(users['COORDINATOR']), cid, 'REJECTED').status_code == 200
    assert not client.get(BASE+'offers/').data
    resource.safe_until = timezone.now()+timedelta(hours=5)
    resource.is_disaster_relief = True
    resource.save()
    assert claim(client, resource).status_code == 400
    resource.is_disaster_relief = False
    resource.save()
    PersonalLocation.objects.filter(user=user).update(latitude=0, longitude=0)
    assert claim(client, resource).status_code == 400
    user.status = 'suspended'
    user.save()
    assert client.get(BASE).status_code == 403


@pytest.mark.django_db(transaction=True)
def test_concurrent_claims_never_overallocate(flow):
    _, resource, _, _ = flow
    people = [personal(f'concurrent{i}@claims.test') for i in range(2)]
    def submit(user):
        try:
            return claim(client_for(user), resource, 15).status_code
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, people))
    assert sorted(results) == [201, 400]
    resource.refresh_from_db()
    assert resource.allocated_quantity == 15 and FoodClaim.objects.count() == 1


@pytest.mark.django_db
def test_authorization_safety_and_weight_capacity(flow):
    users, resource, _, volunteer = flow
    assert APIClient().get(BASE+'offers/').status_code == 403
    user = personal()
    client = client_for(user)
    assert client.patch(BASE, {'status': 'APPROVED'}, format='json').status_code == 405
    no_ack = client.post(BASE, {'resource': resource.pk, 'quantity': 2, 'safetyAcknowledged': False}, format='json')
    assert no_ack.status_code == 400 and not FoodClaim.objects.exists()
    PersonalLocation.objects.create(user=users['FOOD_PROVIDER'], address='Provider', latitude=6.773, longitude=79.8816)
    assert claim(client_for(users['FOOD_PROVIDER']), resource).status_code == 400
    cid = claim(client, resource).data['id']
    assert client.patch(f'{BASE}{cid}/', {'quantity': 100, 'status': 'APPROVED'}, format='json').status_code == 405
    assert step(client_for(users['COORDINATOR']), cid, 'APPROVED').status_code == 200
    volunteer.vehicle_capacity_kg = 1
    volunteer.save()
    assert step(client_for(users['VOLUNTEER']), cid, 'ASSIGNED').status_code == 400
    volunteer.refresh_from_db()
    assert volunteer.status == 'available'
    resource.refresh_from_db()
    assert resource.allocated_quantity == 2
