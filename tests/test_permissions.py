import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRoleAssignment, RoleChoices
from apps.organizations.models import Organization, OrganizationTypeChoices

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
def test_multi_role_user_permissions(client):
    user = User.objects.create_user(
        email='multirole@test.lk',
        password='Password123!',
        full_name='Ravi MultiRole'
    )
    UserRoleAssignment.objects.create(user=user, role=RoleChoices.FOOD_PROVIDER, is_approved=True)
    UserRoleAssignment.objects.create(user=user, role=RoleChoices.VOLUNTEER, is_approved=True)

    client.force_authenticate(user=user)

    assert user.is_food_provider is True
    assert user.is_volunteer is True
    assert user.is_recipient is False
    assert user.is_coordinator is False
    assert set(user.get_approved_roles()) == {'FOOD_PROVIDER', 'VOLUNTEER'}

@pytest.mark.django_db
def test_coordinator_only_verification(client):
    coordinator = User.objects.create_user(
        email='coord@test.lk',
        password='Password123!',
        full_name='Dr. Coordinator'
    )
    UserRoleAssignment.objects.create(user=coordinator, role=RoleChoices.COORDINATOR, is_approved=True)

    regular_user = User.objects.create_user(
        email='regular@test.lk',
        password='Password123!',
        full_name='Regular Volunteer'
    )
    UserRoleAssignment.objects.create(user=regular_user, role=RoleChoices.VOLUNTEER, is_approved=True)

    org = Organization.objects.create(
        name='Test Shelter',
        type=OrganizationTypeChoices.SHELTER,
        contact_email='shelter@test.lk',
        contact_phone='+94 11 222 3344',
        address='123 Test St',
        verified=False
    )

    # Regular user cannot verify organization
    client.force_authenticate(user=regular_user)
    fail_resp = client.post(f'/api/v1/organizations/{org.id}/verify/')
    assert fail_resp.status_code == 403

    # Coordinator can verify organization
    client.force_authenticate(user=coordinator)
    success_resp = client.post(f'/api/v1/organizations/{org.id}/verify/')
    assert success_resp.status_code == 200
    org.refresh_from_db()
    assert org.verified is True
    assert org.verified_by == coordinator
