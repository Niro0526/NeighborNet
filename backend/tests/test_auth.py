import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRoleAssignment, RoleChoices

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
def test_csrf_token_endpoint(client):
    response = client.get('/api/v1/auth/csrf/')
    assert response.status_code == 200
    assert response.data['success'] is True
    assert 'csrfToken' in response.data
    assert len(response.data['csrfToken']) > 0

@pytest.mark.django_db
def test_registration_success(client):
    payload = {
        'email': 'newprovider@test.lk',
        'password': 'StrongPassword123!',
        'full_name': 'Kamal Perera',
        'phone': '+94 77 111 2233',
        'roles': ['FOOD_PROVIDER']
    }
    response = client.post('/api/v1/auth/register/', payload, format='json')
    assert response.status_code == 201
    assert response.data['success'] is True
    assert response.data['user']['email'] == 'newprovider@test.lk'
    assert 'FOOD_PROVIDER' in response.data['user']['assignedRoles']

@pytest.mark.django_db
def test_registration_cannot_self_assign_coordinator(client):
    payload = {
        'email': 'hacker@test.lk',
        'password': 'StrongPassword123!',
        'full_name': 'Malicious User',
        'roles': ['COORDINATOR']
    }
    response = client.post('/api/v1/auth/register/', payload, format='json')
    assert response.status_code == 400
    assert 'Coordinator permissions cannot be self-assigned' in str(response.data)

@pytest.mark.django_db
def test_login_and_logout(client):
    user = User.objects.create_user(
        email='loginuser@test.lk',
        password='ValidPassword123!',
        full_name='Login Test'
    )
    UserRoleAssignment.objects.create(user=user, role=RoleChoices.VOLUNTEER, is_approved=True)

    # 1. Login
    login_resp = client.post('/api/v1/auth/login/', {
        'email': 'loginuser@test.lk',
        'password': 'ValidPassword123!'
    }, format='json')
    assert login_resp.status_code == 200
    assert login_resp.data['success'] is True
    assert login_resp.data['user']['email'] == 'loginuser@test.lk'

    # 2. Get current user
    me_resp = client.get('/api/v1/auth/me/')
    assert me_resp.status_code == 200
    assert me_resp.data['user']['email'] == 'loginuser@test.lk'
    assert 'VOLUNTEER' in me_resp.data['user']['assignedRoles']

    # 3. Logout
    logout_resp = client.post('/api/v1/auth/logout/')
    assert logout_resp.status_code == 200

    # 4. Auth/me should now be unauthorized
    unauth_resp = client.get('/api/v1/auth/me/')
    assert unauth_resp.status_code == 401 or unauth_resp.status_code == 403
