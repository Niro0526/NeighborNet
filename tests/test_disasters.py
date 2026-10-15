import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRoleAssignment, RoleChoices
from apps.organizations.models import Organization, OrganizationTypeChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices, DisasterTypeChoices, DisasterSeverityChoices

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
def test_disaster_activation_coordinator_only(client):
    coord = User.objects.create_user(email='lead@dmc.lk', password='pw')
    UserRoleAssignment.objects.create(user=coord, role=RoleChoices.COORDINATOR, is_approved=True)

    regular = User.objects.create_user(email='regular@test.lk', password='pw')
    UserRoleAssignment.objects.create(user=regular, role=RoleChoices.FOOD_PROVIDER, is_approved=True)

    disaster = DisasterEvent.objects.create(
        title='Flash Floods', description='Flooding in Lowlands',
        status=DisasterStatusChoices.DRAFT, disaster_type=DisasterTypeChoices.FLOOD,
        severity=DisasterSeverityChoices.HIGH
    )

    # Regular user cannot activate
    client.force_authenticate(user=regular)
    fail_resp = client.post(f'/api/v1/disasters/{disaster.id}/activate/')
    assert fail_resp.status_code == 403

    # Coordinator can activate
    client.force_authenticate(user=coord)
    success_resp = client.post(f'/api/v1/disasters/{disaster.id}/activate/')
    assert success_resp.status_code == 200
    disaster.refresh_from_db()
    assert disaster.status == DisasterStatusChoices.ACTIVE
    assert disaster.declared_by == coord

    # Coordinator can resolve
    res_resp = client.post(f'/api/v1/disasters/{disaster.id}/resolve/')
    assert res_resp.status_code == 200
    disaster.refresh_from_db()
    assert disaster.status == DisasterStatusChoices.RESOLVED

@pytest.mark.django_db
def test_disaster_request_must_reference_active_disaster(client):
    recipient_user = User.objects.create_user(email='recip@shelter.lk', password='pw')
    UserRoleAssignment.objects.create(user=recipient_user, role=RoleChoices.RECIPIENT, is_approved=True)
    org = Organization.objects.create(name='Shelter Org', type=OrganizationTypeChoices.SHELTER, contact_email='s@s.lk', contact_phone='1', address='Moratuwa')

    client.force_authenticate(user=recipient_user)
    now = timezone.now()

    # Requisition flagged isDisasterRelief without disaster event must fail validation
    payload = {
        'recipient_id': org.id,
        'item_name': 'Emergency Water',
        'category': 'drinking_water',
        'requestedQuantity': 50.0,
        'unit': 'liters',
        'priority': 'urgent',
        'urgencyDeadline': (now + timedelta(hours=2)).isoformat(),
        'isDisasterRelief': True,
        'disasterEventId': None
    }
    fail_resp = client.post('/api/v1/resource-requests/', payload, format='json')
    assert fail_resp.status_code == 400
    assert 'must reference an active disaster event' in str(fail_resp.data)
