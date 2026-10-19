# NeighborNet AI — Phase 3 API Integration Contract & Checklist

This document details the contract between the React TypeScript frontend and the Django REST Framework backend, tracking the status of each integrated user operation.

---

## 1. Authentication & Session Contracts

| Frontend Operation | Backend Endpoint | HTTP Method | Required Role | Request Payload | Response Shape | Status |
|---|---|---|---|---|---|---|
| CSRF Handshake | `/api/v1/auth/csrf/` | `GET` | Public | None | `{ success: true, csrfToken: string }` | Verified |
| User Sign-In | `/api/v1/auth/login/` | `POST` | Public | `{ email: string, password: string }` | `{ success: true, user: AuthenticatedUser }` | Verified |
| Session Restore | `/api/v1/auth/me/` | `GET` | Authenticated | None | `{ success: true, user: AuthenticatedUser }` | Verified |
| User Sign-Out | `/api/v1/auth/logout/` | `POST` | Authenticated | None | `{ success: true, message: string }` | Verified |
| Org Registration | `/api/v1/auth/register/` | `POST` | Public | `{ email, password, full_name, phone, roles }` | `{ success: true, user: AuthenticatedUser }` | Verified |

---

## 2. Core Operational Contracts

| Frontend Operation | Backend Endpoint | HTTP Method | Required Role | Request Payload | Response Shape | Status |
|---|---|---|---|---|---|---|
| Load Food Listings | `/api/v1/resources/` | `GET` | Authenticated | None | `{ count: number, results: Resource[] }` | Verified |
| Create Surplus Food | `/api/v1/resources/` | `POST` | `FOOD_PROVIDER` | `{ name, category, quantity, unit, pickupStart, pickupEnd, safeUntil, storageRequirements, dietaryTags }` | `Resource` | Verified |
| Withdraw Surplus Food | `/api/v1/resources/{id}/withdraw/` | `POST` | Owner / `COORDINATOR` | None | `{ success: true, resource: Resource }` | Verified |
| Load Requisitions | `/api/v1/resource-requests/` | `GET` | Authenticated | None | `{ count: number, results: ResourceRequest[] }` | Verified |
| Create Requisition | `/api/v1/resource-requests/` | `POST` | `RECIPIENT` | `{ item_name, category, requestedQuantity, unit, priority, urgencyDeadline, peopleImpacted, isDisasterRelief, disasterEventId }` | `ResourceRequest` | Verified |
| Cancel Requisition | `/api/v1/resource-requests/{id}/cancel/` | `POST` | Owner / `COORDINATOR` | None | `{ success: true, request: ResourceRequest }` | Verified |
| Load Delivery Tasks | `/api/v1/delivery-tasks/` | `GET` | Authenticated | None | `{ count: number, results: DeliveryTask[] }` | Verified |
| Accept Task | `/api/v1/delivery-tasks/{id}/accept/` | `POST` | `VOLUNTEER` | None | `{ success: true, task: DeliveryTask }` | Verified |
| Arrived at Pickup | `/api/v1/delivery-tasks/{id}/arrived_pickup/` | `POST` | Assigned Courier | None | `{ success: true, task: DeliveryTask }` | Verified |
| Food Collected | `/api/v1/delivery-tasks/{id}/pickup/` | `POST` | Assigned Courier | None | `{ success: true, task: DeliveryTask }` | Verified |
| Arrived at Delivery | `/api/v1/delivery-tasks/{id}/arrived_delivery/` | `POST` | Assigned Courier | None | `{ success: true, task: DeliveryTask }` | Verified |
| Confirm Delivery | `/api/v1/delivery-tasks/{id}/complete/` | `POST` | Assigned Courier | None | `{ success: true, task: DeliveryTask }` | Verified |
| Report Disruption | `/api/v1/delivery-tasks/{id}/disrupt/` | `POST` | Assigned Courier | `{ reason: string }` | `{ success: true, task: DeliveryTask }` | Verified |
| Courier Availability | `/api/v1/volunteers/toggle_availability/` | `POST` | `VOLUNTEER` | None | `{ success: true, status: string }` | Verified |

---

## 3. Disaster, Allocations & Admin Contracts

| Frontend Operation | Backend Endpoint | HTTP Method | Required Role | Request Payload | Response Shape | Status |
|---|---|---|---|---|---|---|
| Active Disaster Event | `/api/v1/disasters/active/` | `GET` | Authenticated | None | `DisasterEvent` or `null` | Verified |
| List Disaster Events | `/api/v1/disasters/` | `GET` | Authenticated | None | `{ count: number, results: DisasterEvent[] }` | Verified |
| Activate Disaster | `/api/v1/disasters/{id}/activate/` | `POST` | `COORDINATOR` | None | `{ success: true, message: string, disaster: DisasterEvent }` | Verified |
| Resolve Disaster | `/api/v1/disasters/{id}/resolve/` | `POST` | `COORDINATOR` | None | `{ success: true, disaster: DisasterEvent }` | Verified |
| Create Allocation | `/api/v1/allocations/` | `POST` | `COORDINATOR` | `{ resource, request, allocatedQuantity }` | `Allocation` with `deliveryTaskId` | Verified |
| Verify Organization | `/api/v1/organizations/{id}/verify/` | `POST` | `COORDINATOR` | None | `{ success: true, organization: Organization }` | Verified |
| Unified Dashboard | `/api/v1/dashboard/me/` | `GET` | Authenticated | None | `{ user, activeDisaster, providerModule, recipientModule, volunteerModule }` | Verified |
| Admin Command Center | `/api/v1/dashboard/admin/` | `GET` | `COORDINATOR` | None | `{ metrics, pendingAllocations, activeDisasters, recentAlerts }` | Verified |
| Security Audit Logs | `/api/v1/audit/` | `GET` | `COORDINATOR` | None | `{ count: number, results: ActivityLog[] }` | Verified |
| User Notifications | `/api/v1/notifications/` | `GET` | Authenticated | None | `{ count: number, results: Notification[] }` | Verified |
| Mark Read / Mark All | `/api/v1/notifications/{id}/mark_read/` | `POST` | Authenticated | None | `{ success: true }` | Verified |
