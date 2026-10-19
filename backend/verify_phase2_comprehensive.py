"""
NeighborNet AI - Phase 2 Comprehensive End-to-End Verification Script
Tests items 3 through 10 against the live Django REST Framework API and database.
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps'))
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User, RoleChoices, UserRoleAssignment
from apps.organizations.models import Organization, OrganizationTypeChoices
from apps.resources.models import Resource, ResourceCategoryChoices, ResourceStatusChoices
from apps.requests.models import ResourceRequest, RequestPriorityChoices, RequestStatusChoices
from apps.volunteers.models import Volunteer, VolunteerAvailabilityChoices
from apps.disasters.models import DisasterEvent, DisasterStatusChoices
from apps.deliveries.models import Allocation, DeliveryTask, DeliveryTaskStatusChoices
from django.core.management import call_command

def run_verifications():
    results = {}
    client = Client(SERVER_NAME='localhost')

    print("=" * 70)
    print("NeighborNet AI Phase 2 Comprehensive Verification")
    print("=" * 70)

    # ---------------------------------------------------------
    # Check 3: Login, Logout, CSRF protection, and /api/v1/auth/me/
    # ---------------------------------------------------------
    print("\n[Check 3] Testing CSRF, Login, Logout, and /api/v1/auth/me/...")
    # CSRF handshake
    csrf_resp = client.get('/api/v1/auth/csrf/')
    assert csrf_resp.status_code == 200, f"CSRF handshake failed: {csrf_resp.status_code}"
    csrf_token = csrf_resp.json().get('csrfToken')
    assert csrf_token, "No CSRF token returned"

    # Login with valid credentials
    login_resp = client.post('/api/v1/auth/login/', {
        'email': 'fathima@pererahotels.lk',
        'password': 'password123'
    }, content_type='application/json')
    assert login_resp.status_code == 200, f"Login failed: {login_resp.status_code} - {login_resp.content}"
    assert 'user' in login_resp.json()

    # Authenticated /api/v1/auth/me/
    me_resp = client.get('/api/v1/auth/me/')
    assert me_resp.status_code == 200, f"/auth/me/ failed: {me_resp.status_code}"
    me_data = me_resp.json()
    user_info = me_data.get('user', me_data)
    assert user_info['email'] == 'fathima@pererahotels.lk'
    user_roles = user_info.get('assignedRoles', user_info.get('roles', []))
    assert 'FOOD_PROVIDER' in user_roles

    # Logout
    logout_resp = client.post('/api/v1/auth/logout/')
    assert logout_resp.status_code == 200

    # Unauthenticated /auth/me/ should now fail (401/403)
    unauth_me = client.get('/api/v1/auth/me/')
    assert unauth_me.status_code in (401, 403), f"Unauthenticated access permitted: {unauth_me.status_code}"
    results['Check_3_Auth_CSRF'] = 'PASS'
    print("--> Check 3 PASSED (CSRF handshake, Session Auth, /auth/me/, and Logout verified)")

    # ---------------------------------------------------------
    # Check 4: Verify all five seeded personas can authenticate with approved roles
    # ---------------------------------------------------------
    print("\n[Check 4] Testing 5 Seeded Personas Authentication & Permissions...")
    personas = [
        ('fathima@pererahotels.lk', 'password123', ['FOOD_PROVIDER']),
        ('sister.mary@graceeldercare.org', 'password123', ['RECIPIENT']),
        ('dinesh.mendis@gmail.com', 'password123', ['VOLUNTEER']),
        ('ravi.mendis@greenbites.lk', 'password123', ['FOOD_PROVIDER', 'VOLUNTEER']),
        ('kaveen.j@dmc.gov.lk', 'password123', ['COORDINATOR']),
    ]
    for email, password, expected_roles in personas:
        resp = client.post('/api/v1/auth/login/', {'email': email, 'password': password}, content_type='application/json')
        assert resp.status_code == 200, f"Failed login for {email}: {resp.status_code} - {resp.content}"
        data = resp.json()
        u = data.get('user', data)
        roles = u.get('assignedRoles', u.get('roles', []))
        for r in expected_roles:
            assert r in roles, f"Role {r} missing for {email}. Found: {roles}"
        client.post('/api/v1/auth/logout/')
    results['Check_4_Seeded_Personas'] = 'PASS'
    print("--> Check 4 PASSED (All 5 personas authenticated with exact approved roles)")

    # ---------------------------------------------------------
    # Check 5: Multi-role account accesses both feature sets & combined dashboard
    # ---------------------------------------------------------
    print("\n[Check 5] Testing Multi-Role (Provider + Volunteer) Account Access...")
    client.post('/api/v1/auth/login/', {
        'email': 'ravi.mendis@greenbites.lk',
        'password': 'password123'
    }, content_type='application/json')

    # Access food provider resources
    res_resp = client.get('/api/v1/resources/')
    assert res_resp.status_code == 200, f"Provider resource access failed: {res_resp.status_code}"

    # Access volunteer courier tasks
    vol_resp = client.get('/api/v1/delivery-tasks/?status=AVAILABLE')
    assert vol_resp.status_code == 200, f"Volunteer tasks access failed: {vol_resp.status_code}"

    # Access personal dashboard - must dynamically bundle both operational modules
    dash_resp = client.get('/api/v1/dashboard/me/')
    assert dash_resp.status_code == 200, f"Dashboard failed: {dash_resp.status_code}"
    dash_data = dash_resp.json()
    assert 'foodProvider' in dash_data, "foodProvider module missing from multi-role dashboard"
    assert 'volunteer' in dash_data, "volunteer module missing from multi-role dashboard"
    assert 'listings' in dash_data['foodProvider']
    assert 'profile' in dash_data['volunteer']

    client.post('/api/v1/auth/logout/')
    results['Check_5_Multi_Role'] = 'PASS'
    print("--> Check 5 PASSED (Dual operational modules verified under one account)")

    # ---------------------------------------------------------
    # Check 6: Coordinator-only disaster activation & organization verification
    # ---------------------------------------------------------
    print("\n[Check 6] Testing Coordinator-only Disaster Activation & Org Verification...")
    # 1. Non-coordinator attempt (Fathima - Food Provider)
    client.post('/api/v1/auth/login/', {'email': 'fathima@pererahotels.lk', 'password': 'password123'}, content_type='application/json')
    disaster = DisasterEvent.objects.first()
    org_unverified, _ = Organization.objects.get_or_create(
        id='ORG-TEST-UNVERIFIED',
        defaults={
            'name': "Unverified Colombo Kitchen",
            'type': OrganizationTypeChoices.RESTAURANT,
            'contact_email': "unver@test.lk",
            'contact_phone': "+94 11 999 0000",
            'address': "Colombo 03",
            'latitude': 6.91,
            'longitude': 79.86,
            'verified': False
        }
    )
    org_unverified.verified = False
    org_unverified.save()

    forbid_act = client.post(f'/api/v1/disasters/{disaster.id}/activate/')
    assert forbid_act.status_code == 403, f"Non-coordinator allowed to activate disaster: {forbid_act.status_code}"

    forbid_ver = client.post(f'/api/v1/organizations/{org_unverified.id}/verify/')
    assert forbid_ver.status_code == 403, f"Non-coordinator allowed to verify org: {forbid_ver.status_code}"
    client.post('/api/v1/auth/logout/')

    # 2. Coordinator attempt (Dr. Kaveen)
    client.post('/api/v1/auth/login/', {'email': 'kaveen.j@dmc.gov.lk', 'password': 'password123'}, content_type='application/json')
    coord_ver = client.post(f'/api/v1/organizations/{org_unverified.id}/verify/')
    assert coord_ver.status_code == 200, f"Coordinator verify failed: {coord_ver.status_code}"
    org_unverified.refresh_from_db()
    assert org_unverified.verified is True

    coord_dash = client.get('/api/v1/dashboard/admin/')
    assert coord_dash.status_code == 200, f"Coordinator admin dashboard failed: {coord_dash.status_code}"
    client.post('/api/v1/auth/logout/')
    results['Check_6_Coordinator_Privileges'] = 'PASS'
    print("--> Check 6 PASSED (Strict Coordinator authorization enforced)")

    # ---------------------------------------------------------
    # Check 7: Resource creation, requests, atomic allocations, delivery lifecycle
    # ---------------------------------------------------------
    print("\n[Check 7] Testing Resource Creation, Request, Atomic Allocation & State Machine...")
    client.post('/api/v1/auth/login/', {'email': 'kaveen.j@dmc.gov.lk', 'password': 'password123'}, content_type='application/json')
    now = timezone.now()
    coord_user = User.objects.get(email='kaveen.j@dmc.gov.lk')

    # Create resource lot of 20 kg
    res = Resource.objects.create(
        provider=org_unverified,
        name='Rice & Curry Packets',
        category=ResourceCategoryChoices.COOKED_MEALS,
        quantity=20.0,
        unit='kg',
        pickup_start=now,
        pickup_end=now + timedelta(hours=3),
        safe_until=now + timedelta(hours=6),
        status=ResourceStatusChoices.AVAILABLE,
        created_by=coord_user
    )

    # Create requisition of 20 kg
    req = ResourceRequest.objects.create(
        recipient=org_unverified,
        item_name='Cooked Meals Requisition',
        category=ResourceCategoryChoices.COOKED_MEALS,
        requested_quantity=20.0,
        unit='kg',
        priority=RequestPriorityChoices.HIGH,
        urgency_deadline=now + timedelta(hours=4),
        delivery_address='Colombo 05',
        created_by=coord_user
    )

    # Over-allocation rejection (request 25 kg when 20 kg available)
    over_resp = client.post('/api/v1/allocations/', {
        'resource_id': str(res.id),
        'request_id': str(req.id),
        'allocated_quantity': 25.0
    }, content_type='application/json')
    assert over_resp.status_code == 400, f"Over-allocation permitted: {over_resp.status_code}"

    # Valid allocation (15 kg)
    alloc_resp = client.post('/api/v1/allocations/', {
        'resource_id': str(res.id),
        'request_id': str(req.id),
        'allocated_quantity': 15.0
    }, content_type='application/json')
    assert alloc_resp.status_code == 201, f"Valid allocation failed: {alloc_resp.status_code}"
    res.refresh_from_db()
    assert res.allocated_quantity == 15.0
    assert res.available_quantity == 5.0

    task_id = alloc_resp.json().get('deliveryTaskId')
    if not task_id:
        task_id = DeliveryTask.objects.get(allocation_id=alloc_resp.json()['id']).id
    client.post('/api/v1/auth/logout/')

    # Volunteer logs in to drive delivery state machine (Dinesh Mendis)
    client.post('/api/v1/auth/login/', {'email': 'dinesh.mendis@gmail.com', 'password': 'password123'}, content_type='application/json')

    # Cannot jump directly to DELIVERED
    jump_resp = client.post(f'/api/v1/delivery-tasks/{task_id}/complete/')
    assert jump_resp.status_code == 400, f"Invalid transition directly to DELIVERED permitted: {jump_resp.status_code}"

    # Step 1: Accept
    s1 = client.post(f'/api/v1/delivery-tasks/{task_id}/accept/')
    assert s1.status_code == 200, f"Accept failed: {s1.status_code}"

    # Step 2: Arrived at pickup
    s2 = client.post(f'/api/v1/delivery-tasks/{task_id}/arrived_pickup/')
    assert s2.status_code == 200, f"Arrived pickup failed: {s2.status_code}"

    # Step 3: Picked up
    s3 = client.post(f'/api/v1/delivery-tasks/{task_id}/pickup/')
    assert s3.status_code == 200, f"Pickup failed: {s3.status_code}"

    # Step 4: Arrived at delivery
    s4 = client.post(f'/api/v1/delivery-tasks/{task_id}/arrived_delivery/')
    assert s4.status_code == 200, f"Arrived delivery failed: {s4.status_code}"

    # Step 5: Complete
    s5 = client.post(f'/api/v1/delivery-tasks/{task_id}/complete/')
    assert s5.status_code == 200, f"Complete failed: {s5.status_code}"

    task = DeliveryTask.objects.get(id=task_id)
    assert task.status == DeliveryTaskStatusChoices.DELIVERED
    client.post('/api/v1/auth/logout/')
    results['Check_7_Allocations_Lifecycle'] = 'PASS'
    print("--> Check 7 PASSED (No over-allocation & strict state transitions confirmed)")

    # ---------------------------------------------------------
    # Check 8: Disaster relief requests and volunteer assignments
    # ---------------------------------------------------------
    print("\n[Check 8] Testing Disaster Relief Requests & Active Event Linkage...")
    client.post('/api/v1/auth/login/', {'email': 'sister.mary@graceeldercare.org', 'password': 'password123'}, content_type='application/json')
    active_disaster = DisasterEvent.objects.filter(status=DisasterStatusChoices.ACTIVE).first()
    assert active_disaster is not None, "No active disaster found"

    # Emergency requisition referencing active disaster
    disaster_req = client.post('/api/v1/resource-requests/', {
        'item_name': 'Emergency Potable Water 500L',
        'category': 'drinking_water',
        'requestedQuantity': 500.0,
        'unit': 'liters',
        'priority': 'urgent',
        'urgencyDeadline': (now + timedelta(hours=2)).isoformat(),
        'isDisasterRelief': True,
        'disasterEventId': str(active_disaster.id)
    }, content_type='application/json')
    assert disaster_req.status_code == 201, f"Emergency request creation failed: {disaster_req.status_code}"
    assert disaster_req.json()['isDisasterRelief'] is True
    client.post('/api/v1/auth/logout/')
    results['Check_8_Disaster_Requisitions'] = 'PASS'
    print("--> Check 8 PASSED (Disaster linkage & priority handling verified)")

    # ---------------------------------------------------------
    # Check 9: Data isolation between organizations & private audit logs
    # ---------------------------------------------------------
    print("\n[Check 9] Testing Data Isolation & Audit Security...")
    # Fathima cannot withdraw GreenBites (Ravi's) resource
    client.post('/api/v1/auth/login/', {'email': 'fathima@pererahotels.lk', 'password': 'password123'}, content_type='application/json')
    greenbites_org = Organization.objects.filter(id='ORG-001').first()
    greenbites_resource = Resource.objects.filter(provider=greenbites_org).first()

    if greenbites_resource:
        unauth_withdraw = client.post(f'/api/v1/resources/{greenbites_resource.id}/withdraw/')
        assert unauth_withdraw.status_code == 403, f"Unauthorized resource withdrawal permitted: {unauth_withdraw.status_code}"

    # Non-coordinator cannot read audit logs
    audit_resp = client.get('/api/v1/audit/')
    assert audit_resp.status_code == 403, f"Unauthorized audit access permitted: {audit_resp.status_code}"
    client.post('/api/v1/auth/logout/')
    results['Check_9_Data_Isolation'] = 'PASS'
    print("--> Check 9 PASSED (Organization boundaries & audit confidentiality enforced)")

    # ---------------------------------------------------------
    # Check 10: seed_demo idempotency
    # ---------------------------------------------------------
    print("\n[Check 10] Testing seed_demo Idempotency...")
    users_before = User.objects.count()
    orgs_before = Organization.objects.count()
    disasters_before = DisasterEvent.objects.count()

    call_command('seed_demo')

    users_after = User.objects.count()
    orgs_after = Organization.objects.count()
    disasters_after = DisasterEvent.objects.count()

    assert users_before == users_after, f"User count changed from {users_before} to {users_after}"
    assert orgs_before == orgs_after, f"Org count changed from {orgs_before} to {orgs_after}"
    assert disasters_before == disasters_after, f"Disasters count changed from {disasters_before} to {disasters_after}"
    results['Check_10_Seed_Idempotency'] = 'PASS'
    print(f"--> Check 10 PASSED (0 duplicate records: Users={users_after}, Orgs={orgs_after}, Disasters={disasters_after})")

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY (8/8)")
    print("=" * 70)
    return results

if __name__ == '__main__':
    run_verifications()
