"""
End-to-End integration test suite for NeighborNet AI Phase 3 & Phase 5.
Tests scenarios A, B, C, and D through either live Vite/Django server or isolated in-memory Django test client.
"""
import pytest
import requests
import json
import sys
import os
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework.utils.encoders import JSONEncoder

def is_live_server_up(url="http://localhost:5173/api/v1/auth/csrf/"):
    try:
        r = requests.get(url, timeout=0.3)
        return r.status_code == 200
    except Exception:
        return False

USE_LIVE = os.environ.get('NEIGHBORNET_LIVE_TESTS') == '1' and is_live_server_up()
BASE_URL = "http://localhost:5173/api/v1" if USE_LIVE else "/api/v1"

class WrappedResponse:
    def __init__(self, res):
        self._res = res
        self.status_code = res.status_code
        self.content = getattr(res, 'content', b'')
        if isinstance(self.content, bytes):
            self.text = self.content.decode('utf-8')
        else:
            self.text = str(self.content or '')
        self.headers = getattr(res, 'headers', {})

    def json(self):
        if hasattr(self._res, 'data') and self._res.data is not None:
            return json.loads(json.dumps(self._res.data, cls=JSONEncoder))
        if self.text:
            try:
                return json.loads(self.text)
            except Exception:
                return {}
        return {}

class InMemoryTestSession:
    def __init__(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.headers = {}
        self.cookies = {}
        r = self.client.get('/api/v1/auth/csrf/')
        token = r.data.get('csrfToken', 'test-csrf-token')
        self.headers["X-CSRFToken"] = token
        self.cookies["csrftoken"] = token
        # Inject csrftoken into client cookies so CSRF middleware can validate header against cookie
        self.client.cookies['csrftoken'] = token

    def get(self, url, **kwargs):
        path = url.replace("http://localhost:5173", "").replace("http://127.0.0.1:8000", "")
        extra = {}
        if "X-CSRFToken" in self.headers:
            extra["HTTP_X_CSRFTOKEN"] = self.headers["X-CSRFToken"]
        res = self.client.get(path, **extra)
        return WrappedResponse(res)

    def post(self, url, json=None, **kwargs):
        path = url.replace("http://localhost:5173", "").replace("http://127.0.0.1:8000", "")
        extra = {}
        if "X-CSRFToken" in self.headers:
            extra["HTTP_X_CSRFTOKEN"] = self.headers["X-CSRFToken"]
        res = self.client.post(path, data=json or {}, format='json', **extra)
        if 'csrftoken' in self.client.cookies:
            val = self.client.cookies['csrftoken']
            self.cookies['csrftoken'] = val.value if hasattr(val, 'value') else str(val)
        return WrappedResponse(res)

@pytest.fixture(autouse=True)
def setup_seed_data(db):
    if not USE_LIVE:
        call_command('seed_demo', force=True)

def create_session():
    if USE_LIVE:
        s = requests.Session()
        r = s.get(f"{BASE_URL}/auth/csrf/")
        assert r.status_code == 200, f"Failed to get CSRF token: {r.status_code} {r.text}"
        csrf_token = r.cookies.get("csrftoken") or r.json().get("csrfToken")
        s.headers.update({
            "X-CSRFToken": csrf_token,
            "Referer": "http://localhost:5173/",
        })
        return s
    else:
        return InMemoryTestSession()

def login(session, email, password="password123"):
    r = session.post(f"{BASE_URL}/auth/login/", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    new_csrf = session.cookies.get("csrftoken")
    if new_csrf:
        session.headers["X-CSRFToken"] = new_csrf
    return r.json()

@pytest.mark.django_db
def test_scenario_a_food_rescue():
    print("=== Testing Scenario A: Food Rescue Workflow ===")
    
    # 1. Food Provider logs in
    s_provider = create_session()
    user_p = login(s_provider, "fathima@pererahotels.lk")
    print(f"  [+] Logged in as Provider: {user_p['user']['email']}, roles: {user_p['user']['assignedRoles']}")
    
    # 2. Provider creates a food listing
    food_payload = {
        "name": "Fresh Surplus Veg Meal Packs",
        "category": "cooked_meals",
        "quantity": 25.0,
        "unit": "kg",
        "dietaryTags": ["Vegetarian", "Halal"],
        "storageRequirements": "Ambient",
        "pickupStart": "2026-10-10T12:00:00Z",
        "pickupEnd": "2026-10-11T18:00:00Z",
        "safeUntil": "2026-10-11T20:00:00Z",
    }
    r = s_provider.post(f"{BASE_URL}/resources/", json=food_payload)
    assert r.status_code == 201, f"Create food listing failed: {r.status_code} {r.text}"
    resource = r.json()
    resource_id = resource["id"]
    print(f"  [+] Created Resource Listing ID: {resource_id}, quantity: {resource['quantity']} {resource['unit']}")
    
    # 3. Recipient logs in and creates a resource request
    s_recipient = create_session()
    user_r = login(s_recipient, "sister.mary@graceeldercare.org")
    print(f"  [+] Logged in as Recipient: {user_r['user']['email']}, roles: {user_r['user']['assignedRoles']}")
    
    req_payload = {
        "item_name": "Elderly Care Lunch Supplies",
        "category": "cooked_meals",
        "requestedQuantity": 20.0,
        "unit": "kg",
        "priority": "high",
        "urgencyDeadline": "2026-10-11T14:00:00Z",
        "peopleImpacted": 40,
    }
    r = s_recipient.post(f"{BASE_URL}/resource-requests/", json=req_payload)
    assert r.status_code == 201, f"Create resource request failed: {r.status_code} {r.text}"
    request_obj = r.json()
    request_id = request_obj["id"]
    print(f"  [+] Created Resource Request ID: {request_id}, requested: {request_obj.get('requestedQuantity')} {request_obj.get('unit')}")
    
    # 4. Coordinator logs in and creates an allocation
    s_coord = create_session()
    user_c = login(s_coord, "kaveen.j@dmc.gov.lk")
    print(f"  [+] Logged in as Coordinator: {user_c['user']['email']}, roles: {user_c['user']['assignedRoles']}")
    
    alloc_payload = {
        "resource": resource_id,
        "request": request_id,
        "allocatedQuantity": 20.0,
        "notes": "Coordinated dispatch for elderly shelter lunch.",
    }
    r = s_coord.post(f"{BASE_URL}/allocations/", json=alloc_payload)
    assert r.status_code == 201, f"Create allocation failed: {r.status_code} {r.text}"
    allocation = r.json()
    alloc_id = allocation["id"]
    delivery_task_id = allocation.get("deliveryTaskId") or allocation.get("delivery_task")
    print(f"  [+] Created Allocation ID: {alloc_id}, Delivery Task ID: {delivery_task_id}")
    
    # 5. Volunteer logs in
    s_vol = create_session()
    user_v = login(s_vol, "dinesh.mendis@gmail.com")
    print(f"  [+] Logged in as Volunteer: {user_v['user']['email']}, roles: {user_v['user']['assignedRoles']}")
    
    # Check delivery task exists
    r = s_vol.get(f"{BASE_URL}/delivery-tasks/{delivery_task_id}/")
    assert r.status_code == 200, f"Get delivery task failed: {r.status_code} {r.text}"
    task = r.json()
    print(f"  [+] Task Initial Status: {task['status']}")
    
    # 6. Volunteer transitions delivery task: ACCEPTED -> ARRIVED_PICKUP -> PICKED_UP -> ARRIVED_DELIVERY -> DELIVERED
    r = s_vol.post(f"{BASE_URL}/delivery-tasks/{delivery_task_id}/accept/")
    assert r.status_code == 200, f"Accept task failed: {r.status_code} {r.text}"
    status_val = r.json().get('task', {}).get('status') or r.json().get('status')
    print(f"  [+] Transitioned to: {status_val}")
    
    r = s_vol.post(f"{BASE_URL}/delivery-tasks/{delivery_task_id}/arrived_pickup/")
    assert r.status_code == 200, f"Arrived pickup failed: {r.status_code} {r.text}"
    status_val = r.json().get('task', {}).get('status') or r.json().get('status')
    print(f"  [+] Transitioned to: {status_val}")
    
    r = s_vol.post(f"{BASE_URL}/delivery-tasks/{delivery_task_id}/pickup/")
    assert r.status_code == 200, f"Pickup failed: {r.status_code} {r.text}"
    status_val = r.json().get('task', {}).get('status') or r.json().get('status')
    print(f"  [+] Transitioned to: {status_val}")
    
    r = s_vol.post(f"{BASE_URL}/delivery-tasks/{delivery_task_id}/arrived_delivery/")
    assert r.status_code == 200, f"Arrived delivery failed: {r.status_code} {r.text}"
    status_val = r.json().get('task', {}).get('status') or r.json().get('status')
    print(f"  [+] Transitioned to: {status_val}")
    
    r = s_vol.post(f"{BASE_URL}/delivery-tasks/{delivery_task_id}/complete/")
    assert r.status_code == 200, f"Complete delivery failed: {r.status_code} {r.text}"
    final_status = r.json().get('task', {}).get('status') or r.json().get('status')
    print(f"  [+] Final Delivery Task Status: {final_status}")
    assert final_status == "DELIVERED"
    
    # 7. Check user dashboard
    r = s_vol.get(f"{BASE_URL}/dashboard/me/")
    assert r.status_code == 200, f"Volunteer dashboard failed: {r.status_code} {r.text}"
    v_dash = r.json()
    print(f"  [+] Volunteer Dashboard Loaded: Roles = {v_dash['user']['assignedRoles']}")
    print("  [SUCCESS] Scenario A fully verified!\n")

@pytest.mark.django_db
def test_scenario_b_multirole():
    print("=== Testing Scenario B: Multi-Role Account Workflow ===")
    s = create_session()
    # Ravi Mendis has both FOOD_PROVIDER and VOLUNTEER roles
    res = login(s, "ravi.mendis@greenbites.lk")
    roles = res['user']['assignedRoles']
    print(f"  [+] Logged in as: {res['user']['email']}, Approved Roles: {roles}")
    assert "FOOD_PROVIDER" in roles and "VOLUNTEER" in roles, f"Expected multi-role, got {roles}"
    
    # Verify user dashboard reflects multi-role modules
    r = s.get(f"{BASE_URL}/dashboard/me/")
    assert r.status_code == 200, f"Dashboard failed: {r.status_code}"
    dash_data = r.json()
    dash_roles = dash_data["user"]["assignedRoles"]
    assert "FOOD_PROVIDER" in dash_roles and "VOLUNTEER" in dash_roles
    print(f"  [+] Unified Dashboard reflects both roles in single view without role switching: {dash_roles}")
    
    # Verify authorized food operations
    r = s.get(f"{BASE_URL}/resources/")
    assert r.status_code == 200
    print(f"  [+] Food Provider Resources accessible (count: {len(r.json().get('results', r.json()))})")
    
    # Verify authorized volunteer operations under the exact same session
    r = s.get(f"{BASE_URL}/delivery-tasks/")
    assert r.status_code == 200
    print(f"  [+] Volunteer Delivery Tasks accessible (count: {len(r.json().get('results', r.json()))})")
    print("  [SUCCESS] Scenario B fully verified!\n")

@pytest.mark.django_db
def test_scenario_c_disaster_response():
    print("=== Testing Scenario C: Disaster Response Workflow ===")
    s_coord = create_session()
    login(s_coord, "kaveen.j@dmc.gov.lk")
    
    # List disasters
    r = s_coord.get(f"{BASE_URL}/disasters/")
    assert r.status_code == 200
    disasters = r.json().get('results', r.json())
    assert len(disasters) > 0, "No disaster events found"
    disaster_id = disasters[0]["id"]
    print(f"  [+] Found Disaster ID: {disaster_id}, Title: {disasters[0]['title']}")
    
    # Activate disaster
    r = s_coord.post(f"{BASE_URL}/disasters/{disaster_id}/activate/")
    assert r.status_code == 200, f"Activate disaster failed: {r.status_code} {r.text}"
    disaster_status = r.json().get('disaster', {}).get('status') or r.json().get('status')
    print(f"  [+] Disaster Status after activation: {disaster_status}")
    
    # Query active disasters
    r = s_coord.get(f"{BASE_URL}/disasters/active/")
    assert r.status_code == 200
    active_disaster = r.json()
    assert active_disaster is not None, "Expected an active disaster"
    print(f"  [+] Confirmed active disaster returned: {active_disaster['title']}")
    
    # Recipient submits emergency relief request referencing active disaster
    s_rec = create_session()
    login(s_rec, "sister.mary@graceeldercare.org")
    em_payload = {
        "item_name": "Emergency Drinking Water Supply",
        "category": "drinking_water",
        "requestedQuantity": 500.0,
        "unit": "liters",
        "priority": "urgent",
        "disasterEventId": disaster_id,
        "isDisasterRelief": True,
        "urgencyDeadline": "2026-10-12T12:00:00Z",
        "peopleImpacted": 120,
    }
    r = s_rec.post(f"{BASE_URL}/resource-requests/", json=em_payload)
    assert r.status_code == 201, f"Create emergency request failed: {r.status_code} {r.text}"
    em_req = r.json()
    print(f"  [+] Emergency Request Created ID: {em_req['id']}, Linked Disaster: {em_req.get('disasterEventId') or em_req.get('disaster_event_id')}")
    
    # Non-coordinator cannot activate disasters (Security test)
    r = s_rec.post(f"{BASE_URL}/disasters/{disaster_id}/activate/")
    assert r.status_code == 403, f"Expected 403 for recipient activating disaster, got {r.status_code}"
    print(f"  [+] Non-coordinator correctly rejected with HTTP {r.status_code} Forbidden")
    print("  [SUCCESS] Scenario C fully verified!\n")

@pytest.mark.django_db
def test_scenario_d_security_and_integrity():
    print("=== Testing Scenario D: Security & Constraints Integrity ===")
    
    # 1. Unauthenticated request to /auth/me/
    if USE_LIVE:
        s_unauth = requests.Session()
    else:
        s_unauth = InMemoryTestSession()
    r = s_unauth.get(f"{BASE_URL}/auth/me/")
    assert r.status_code in (401, 403), f"Expected 401/403 for unauthenticated, got {r.status_code}"
    print(f"  [+] Unauthenticated /auth/me/ rejected with HTTP {r.status_code}")
    
    # 2. CSRF enforcement on authenticated POST without token
    s_auth_nocsrf = create_session()
    login(s_auth_nocsrf, "fathima@pererahotels.lk")
    if "X-CSRFToken" in s_auth_nocsrf.headers:
        del s_auth_nocsrf.headers["X-CSRFToken"]
    r = s_auth_nocsrf.post(f"{BASE_URL}/resources/", json={"name": "Test Lot"})
    assert r.status_code == 403, f"Expected 403 CSRF failure, got {r.status_code}"
    print(f"  [+] Authenticated request without CSRF token rejected with HTTP {r.status_code}: {r.json().get('detail')}")
    
    # 3. Regular user forbidden from Coordinator admin dashboard
    s_reg = create_session()
    login(s_reg, "dinesh.mendis@gmail.com")
    r = s_reg.get(f"{BASE_URL}/dashboard/admin/")
    assert r.status_code == 403, f"Expected 403 for volunteer accessing admin dashboard, got {r.status_code}"
    print(f"  [+] Volunteer accessing Coordinator dashboard rejected with HTTP {r.status_code}")
    
    # 4. Over-allocation quantity rejected
    s_coord = create_session()
    login(s_coord, "kaveen.j@dmc.gov.lk")
    # Fetch an available resource
    r = s_coord.get(f"{BASE_URL}/resources/")
    resources = r.json().get('results', r.json())
    avail_res = [res for res in resources if float(res.get('availableQuantity') or res.get('available_quantity') or 0) > 0][0]
    
    # Fetch an open request
    r = s_coord.get(f"{BASE_URL}/resource-requests/")
    requests_list = r.json().get('results', r.json())
    avail_req = requests_list[0]
    
    avail_qty = float(avail_res.get('availableQuantity') or avail_res.get('available_quantity') or 0)
    excess_qty = avail_qty + 99999.00
    alloc_invalid = {
        "resource": avail_res["id"],
        "request": avail_req["id"],
        "allocatedQuantity": excess_qty,
    }
    r = s_coord.post(f"{BASE_URL}/allocations/", json=alloc_invalid)
    assert r.status_code in (400, 422), f"Expected 400 for over-allocation, got {r.status_code} {r.text}"
    print(f"  [+] Over-allocation exceeding inventory rejected with HTTP {r.status_code}: {r.json()}")
    
    print("  [SUCCESS] Scenario D fully verified!\n")

if __name__ == "__main__":
    try:
        test_scenario_a_food_rescue()
        test_scenario_b_multirole()
        test_scenario_c_disaster_response()
        test_scenario_d_security_and_integrity()
        print("************************************************************")
        print("ALL END-TO-END SCENARIOS A, B, C, D PASSED SUCCESSFULLY!")
        print("************************************************************")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
