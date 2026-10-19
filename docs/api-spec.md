# NeighborNet AI — REST API Specification (v1)

Base URL: `http://localhost:8000/api/v1/`

All endpoints accept and return JSON. Authenticated endpoints require an active Django session cookie (`sessionid`) and CSRF header (`X-CSRFToken`) for state-changing HTTP methods.

---

## 1. Authentication & Identity (`/auth/`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/auth/csrf/` | Retrieve CSRF cookie & token | None |
| `POST` | `/auth/login/` | Authenticate user & issue session cookie | None |
| `POST` | `/auth/logout/` | Terminate session & clear cookies | Session |
| `GET` | `/auth/me/` | Current user profile, approved roles, permissions | Session |
| `POST` | `/auth/register/` | Register new user account (self-assigns non-coordinator roles) | None |

### `GET /auth/csrf/`
**Response (200 OK):**
```json
{
  "csrfToken": "abc123xyz...",
  "detail": "CSRF cookie set successfully."
}
```

### `POST /auth/login/`
**Request Payload:**
```json
{
  "email": "chef.sunil@colombobites.lk",
  "password": "DemoPass123!"
}
```
**Response (200 OK):**
```json
{
  "user": {
    "id": "c1f10001-0000-0000-0000-000000000001",
    "email": "chef.sunil@colombobites.lk",
    "name": "Sunil Shantha",
    "phone": "+94 77 123 4567",
    "roles": ["FOOD_PROVIDER"],
    "isApproved": true,
    "isStaff": false
  },
  "roles": ["FOOD_PROVIDER"],
  "organizations": ["Colombo City Bakery"]
}
```

---

## 2. Personal & Admin Dashboards (`/dashboard/`)

### `GET /dashboard/me/`
Dynamic aggregation endpoint that introspects the user's active approved roles and bundles operational feeds into a unified JSON object.

**Response (200 OK):**
```json
{
  "activeDisaster": null,
  "foodProvider": {
    "totalDonatedKg": 210.5,
    "activeListingsCount": 4,
    "listings": [...],
    "pendingPickups": [...]
  },
  "volunteer": {
    "profile": {...},
    "activeMission": null,
    "availableTasks": [...],
    "completedCount": 14
  }
}
```

### `GET /dashboard/admin/`
Coordinator Command Center summary (Strictly restricted to users with `COORDINATOR` role).

**Response (200 OK):**
```json
{
  "metrics": {
    "activeVolunteersCount": 8,
    "openRequestsCount": 3,
    "availableResourcesKg": 145.0,
    "activeDisaster": "Kelani River Flash Floods 2026",
    "disasterStatus": "ACTIVE"
  },
  "unverifiedOrganizations": [...],
  "unverifiedVolunteers": [...],
  "recentDisasters": [...],
  "recentAuditLogs": [...]
}
```

---

## 3. Organizations (`/organizations/`)

| Method | Endpoint | Description | Perms |
|---|---|---|---|
| `GET` | `/organizations/` | List registered organizations | IsAuthenticated |
| `POST` | `/organizations/` | Register new organization | IsAuthenticated |
| `GET` | `/organizations/{id}/` | Organization details | IsAuthenticated |
| `POST` | `/organizations/{id}/verify/` | Mark organization verified | Coordinator Only |

---

## 4. Resources Inventory (`/resources/`)

| Method | Endpoint | Description | Perms |
|---|---|---|---|
| `GET` | `/resources/` | Filter resources (`?status=`, `?category=`, `?disaster=`) | IsAuthenticated |
| `POST` | `/resources/` | Create surplus food or relief resource | Food Provider / Coordinator |
| `GET` | `/resources/{id}/` | Resource lot details | IsAuthenticated |
| `POST` | `/resources/{id}/withdraw/` | Withdraw inventory from circulation | Owner Org / Coordinator |

---

## 5. Recipient Resource Requests (`/resource-requests/`)

| Method | Endpoint | Description | Perms |
|---|---|---|---|
| `GET` | `/resource-requests/` | List recipient requisitions | IsAuthenticated |
| `POST` | `/resource-requests/` | Create resource request | Recipient / Coordinator |
| `GET` | `/resource-requests/{id}/` | Request details | IsAuthenticated |
| `POST` | `/resource-requests/{id}/cancel/` | Cancel requisition | Recipient / Coordinator |

---

## 6. Allocations (`/allocations/`)

| Method | Endpoint | Description | Perms |
|---|---|---|---|
| `GET` | `/allocations/` | List inventory allocations | IsAuthenticated |
| `POST` | `/allocations/` | Create atomic allocation (reserves quantity) | Coordinator Only |

**Request Payload:**
```json
{
  "resource_id": "uuid",
  "request_id": "uuid",
  "allocated_quantity": 25.0
}
```

---

## 7. Delivery Tasks (`/delivery-tasks/`)

| Method | Endpoint | Description | Perms |
|---|---|---|---|
| `GET` | `/delivery-tasks/` | List delivery tasks (`?status=`, `?mine=true`) | IsAuthenticated |
| `POST` | `/delivery-tasks/{id}/accept/` | Volunteer accepts task | Verified Volunteer |
| `POST` | `/delivery-tasks/{id}/arrived_pickup/` | Volunteer arrived at pickup location | Assigned Volunteer |
| `POST` | `/delivery-tasks/{id}/pickup/` | Confirm item collected | Assigned Volunteer |
| `POST` | `/delivery-tasks/{id}/arrived_delivery/` | Volunteer arrived at delivery destination | Assigned Volunteer |
| `POST` | `/delivery-tasks/{id}/complete/` | Mark task DELIVERED | Assigned Volunteer |
| `POST` | `/delivery-tasks/{id}/disrupt/` | Mark delivery DISRUPTED with reason | Assigned Volunteer |

---

## 8. Volunteers (`/volunteers/`)

| Method | Endpoint | Description | Perms |
|---|---|---|---|
| `GET` | `/volunteers/` | List volunteers | IsAuthenticated |
| `GET` | `/volunteers/{id}/` | Volunteer profile details | IsAuthenticated |
| `POST` | `/volunteers/toggle_availability/` | Toggle available/offline state | Volunteer Self |
| `POST` | `/volunteers/{id}/verify/` | Mark volunteer verified | Coordinator Only |

---

## 9. Disaster Events (`/disasters/`)

| Method | Endpoint | Description | Perms |
|---|---|---|---|
| `GET` | `/disasters/` | List disaster events | IsAuthenticated |
| `GET` | `/disasters/active/` | Get currently active disaster event | IsAuthenticated |
| `POST` | `/disasters/` | Create new disaster event draft | Coordinator Only |
| `POST` | `/disasters/{id}/activate/` | Activate disaster emergency mode | Coordinator Only |
| `POST` | `/disasters/{id}/resolve/` | Mark disaster emergency resolved | Coordinator Only |

---

## 10. Notifications (`/notifications/`) & Audit Logs (`/audit/`)

| Method | Endpoint | Description | Perms |
|---|---|---|---|
| `GET` | `/notifications/` | List user's notifications | IsAuthenticated |
| `POST` | `/notifications/{id}/mark_read/` | Mark notification read | Owner |
| `POST` | `/notifications/mark_all_read/` | Mark all user notifications read | Owner |
| `GET` | `/audit/` | View system activity & security logs | Coordinator Only |
