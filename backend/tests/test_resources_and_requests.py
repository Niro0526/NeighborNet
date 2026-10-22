import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRoleAssignment, RoleChoices
from apps.organizations.models import Organization, OrganizationTypeChoices, OrganizationMembership, MembershipRoleChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
def test_resource_creation_and_positive_quantity_validation(client):
    provider_user = User.objects.create_user(email='bakery@test.lk', password='pw', full_name='Baker')
    UserRoleAssignment.objects.create(user=provider_user, role=RoleChoices.FOOD_PROVIDER, is_approved=True)

    org = Organization.objects.create(
        name='Artisan Bakery', type=OrganizationTypeChoices.BAKERY, verified=True,
        contact_email='b@test.lk', contact_phone='+94 11 000 1111', address='Katubedda'
    )
    OrganizationMembership.objects.create(organization=org, user=provider_user, role=MembershipRoleChoices.OWNER)

    client.force_authenticate(user=provider_user)
    now = timezone.now()

    # 1. Valid food creation
    payload = {
        'name': 'Fresh Sourdough Loaves',
        'category': 'bakery',
        'quantity': 25.0,
        'unit': 'kg',
        'pickupStart': now.isoformat(),
        'pickupEnd': (now + timedelta(hours=4)).isoformat(),
        'safeUntil': (now + timedelta(hours=24)).isoformat(),
        'storageRequirements': 'Ambient',
        'provider_id': org.id
    }
    resp = client.post('/api/v1/resources/', payload, format='json')
    assert resp.status_code == 201
    assert resp.data['availableQuantity'] == 25.0

    # 2. Invalid non-positive quantity rejection
    invalid_payload = payload.copy()
    invalid_payload['quantity'] = -5.0
    fail_resp = client.post('/api/v1/resources/', invalid_payload, format='json')
    assert fail_resp.status_code == 400

@pytest.mark.django_db
def test_expired_resource_auto_exclusion(client):
    provider_user = User.objects.create_user(email='p@test.lk', password='pw')
    UserRoleAssignment.objects.create(user=provider_user, role=RoleChoices.FOOD_PROVIDER, is_approved=True)
    org = Organization.objects.create(name='P Org', type=OrganizationTypeChoices.RESTAURANT, contact_email='p@o.lk', contact_phone='123', address='Test')

    client.force_authenticate(user=provider_user)
    now = timezone.now()

    # Active fresh food
    r_fresh = Resource.objects.create(
        provider=org, name='Fresh Rolls', category=ResourceCategoryChoices.BAKERY,
        quantity=10.0, pickup_start=now, pickup_end=now + timedelta(hours=2),
        safe_until=now + timedelta(hours=10), status=ResourceStatusChoices.AVAILABLE
    )

    # Food whose safe_until has already passed
    r_expired = Resource.objects.create(
        provider=org, name='Old Soup', category=ResourceCategoryChoices.COOKED_MEALS,
        quantity=5.0, pickup_start=now - timedelta(hours=12), pickup_end=now - timedelta(hours=8),
        safe_until=now - timedelta(hours=2), status=ResourceStatusChoices.AVAILABLE
    )

    # Query with status=AVAILABLE
    resp = client.get('/api/v1/resources/?status=AVAILABLE')
    assert resp.status_code == 200
    names = [item['name'] for item in resp.data['results']]
    assert 'Fresh Rolls' in names
    assert 'Old Soup' not in names

    r_expired.refresh_from_db()
    assert r_expired.status == ResourceStatusChoices.EXPIRED
