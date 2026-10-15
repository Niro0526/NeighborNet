import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRoleAssignment, RoleChoices
from apps.organizations.models import Organization, OrganizationTypeChoices, OrganizationMembership, MembershipRoleChoices

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
def test_unified_personal_dashboard_multirole(client):
    user = User.objects.create_user(
        email='ravi@greenbites.lk',
        password='pw',
        full_name='Ravi Mendis'
    )
    UserRoleAssignment.objects.create(user=user, role=RoleChoices.FOOD_PROVIDER, is_approved=True)
    UserRoleAssignment.objects.create(user=user, role=RoleChoices.VOLUNTEER, is_approved=True)

    org = Organization.objects.create(name='GreenBites', type=OrganizationTypeChoices.BAKERY, contact_email='g@b.lk', contact_phone='1', address='Moratuwa')
    OrganizationMembership.objects.create(organization=org, user=user, role=MembershipRoleChoices.OWNER)

    client.force_authenticate(user=user)

    resp = client.get('/api/v1/dashboard/me/')
    assert resp.status_code == 200

    # User info
    assert resp.data['user']['email'] == 'ravi@greenbites.lk'
    assert 'FOOD_PROVIDER' in resp.data['user']['assignedRoles']
    assert 'VOLUNTEER' in resp.data['user']['assignedRoles']

    # Both modules must be included in the combined response!
    assert 'foodProvider' in resp.data
    assert 'volunteer' in resp.data
    assert 'recipient' not in resp.data

@pytest.mark.django_db
def test_coordinator_dashboard_security(client):
    regular = User.objects.create_user(email='v@test.lk', password='pw')
    UserRoleAssignment.objects.create(user=regular, role=RoleChoices.VOLUNTEER, is_approved=True)

    coord = User.objects.create_user(email='c@dmc.lk', password='pw', full_name='Dr. Kaveen')
    UserRoleAssignment.objects.create(user=coord, role=RoleChoices.COORDINATOR, is_approved=True)

    # 1. Regular volunteer cannot access admin dashboard
    client.force_authenticate(user=regular)
    fail_resp = client.get('/api/v1/dashboard/admin/')
    assert fail_resp.status_code == 403

    # 2. Coordinator accesses admin dashboard successfully
    client.force_authenticate(user=coord)
    success_resp = client.get('/api/v1/dashboard/admin/')
    assert success_resp.status_code == 200
    assert 'kpis' in success_resp.data
    assert 'pendingApprovals' in success_resp.data
    assert 'availableSurplusKg' in success_resp.data['kpis']
