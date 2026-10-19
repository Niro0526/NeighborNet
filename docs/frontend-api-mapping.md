# NeighborNet AI — Frontend Mock Service to Backend API Mapping

This document details the correspondence between the Phase 1 React TypeScript services (`frontend/src/services/`) and the Phase 2 Django REST Framework endpoints.

---

## 1. Authentication Service (`frontend/src/services/authService.ts`)

| Frontend Method | Phase 1 Mock Behavior | Phase 2 Backend Endpoint | HTTP Method |
|---|---|---|---|
| `login(email, password)` | Reads `MOCK_USERS` by email | `/api/v1/auth/login/` | `POST` |
| `logout()` | Clears `localStorage` | `/api/v1/auth/logout/` | `POST` |
| `getCurrentUser()` | Reads `localStorage` | `/api/v1/auth/me/` | `GET` |
| `getCsrfToken()` | N/A | `/api/v1/auth/csrf/` | `GET` |
| `register(data)` | Appends to memory | `/api/v1/auth/register/` | `POST` |

> [!NOTE]
> In Phase 3, `login()` should first call `GET /api/v1/auth/csrf/` to seed the `csrftoken` cookie before dispatching the credentials. Axios should configure `withCredentials: true`.

---

## 2. Food Rescue Service (`frontend/src/services/foodRescueService.ts`)

| Frontend Method | Phase 1 Mock | Phase 2 Backend Endpoint | Notes |
|---|---|---|---|
| `getFoodListings()` | Returns `MOCK_FOOD_LISTINGS` | `GET /api/v1/resources/?category=food` | Filterable by `status=AVAILABLE` |
| `createFoodListing(data)` | In-memory append | `POST /api/v1/resources/` | Validates positive quantity & window |
| `getFoodListingById(id)` | Finds by ID | `GET /api/v1/resources/{id}/` | Full lot details |
| `withdrawListing(id)` | Mutates status | `POST /api/v1/resources/{id}/withdraw/` | Requires owner or coordinator |

---

## 3. Disaster Service (`frontend/src/services/disasterService.ts`)

| Frontend Method | Phase 1 Mock | Phase 2 Backend Endpoint | Notes |
|---|---|---|---|
| `getActiveDisaster()` | Static flood object | `GET /api/v1/disasters/active/` | Returns 200 with object or `active: false` |
| `getDisasters()` | Array of mock disasters | `GET /api/v1/disasters/` | Paginated event list |
| `activateDisaster(id)` | Sets `status: active` | `POST /api/v1/disasters/{id}/activate/` | **Coordinator only** |
| `resolveDisaster(id)` | Sets `status: resolved`| `POST /api/v1/disasters/{id}/resolve/` | **Coordinator only** |

---

## 4. Volunteer Service (`frontend/src/services/volunteerService.ts`)

| Frontend Method | Phase 1 Mock | Phase 2 Backend Endpoint | Notes |
|---|---|---|---|
| `getVolunteerProfile(id)`| Mock profile | `GET /api/v1/volunteers/{id}/` | Location stripped unless owner/admin |
| `toggleAvailability()` | Flips boolean | `POST /api/v1/volunteers/toggle_availability/` | Toggles `available` / `offline` |
| `getAvailableTasks()` | Filters mock tasks | `GET /api/v1/delivery-tasks/?status=AVAILABLE` | Courier dispatch pool |
| `acceptTask(taskId)` | Updates task | `POST /api/v1/delivery-tasks/{id}/accept/` | State machine transition |
| `updateTaskStatus(taskId, st)`| Mutates status | Dedicated endpoint: `/pickup/`, `/complete/` | Strict order enforced |

---

## 5. Coordinator Service (`frontend/src/services/coordinatorService.ts`)

| Frontend Method | Phase 1 Mock | Phase 2 Backend Endpoint | Notes |
|---|---|---|---|
| `getDashboardOverview()`| Hardcoded KPI sums | `GET /api/v1/dashboard/admin/` | Real database aggregates |
| `verifyOrganization(id)`| Sets `isVerified: true` | `POST /api/v1/organizations/{id}/verify/` | Audit log recorded |
| `createAllocation(data)`| Deducts mock quantity | `POST /api/v1/allocations/` | Atomic `select_for_update` lock |
| `getAuditLogs()` | Returns mock logs | `GET /api/v1/audit/` | Filterable by role / action |

---

## 6. Personal Dashboard (`frontend/src/pages/UnifiedDashboardPage.tsx`)

| Frontend View Module | Phase 2 Combined Backend Endpoint |
|---|---|
| Unified Dashboard (Food Provider + Recipient + Volunteer) | `GET /api/v1/dashboard/me/` |

Instead of making 4 separate REST calls on initial dashboard load, the frontend can query `GET /api/v1/dashboard/me/`, which dynamically returns only the sections corresponding to the user's approved roles.

---

## 7. Field Case Compatibility

All Phase 2 serializers use camelCase alias mapping:
- `pickup_start` ↔ `pickupStart`
- `pickup_end` ↔ `pickupEnd`
- `safe_until` ↔ `safeUntil`
- `storage_requirements` ↔ `storageRequirements`
- `requested_quantity` ↔ `requestedQuantity`
- `is_disaster_relief` ↔ `isDisasterRelief`
- `vehicle_type` ↔ `vehicleType`
- `vehicle_capacity_kg` ↔ `vehicleCapacityKg`

Existing TypeScript interfaces in `frontend/src/types/` remain directly compatible with zero required schema alterations.
