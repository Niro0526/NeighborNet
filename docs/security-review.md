# NeighborNet AI — Security and Data Integrity Audit (Phase 5)

## 1. Executive Summary

NeighborNet AI Phase 5 enforces defense-in-depth security principles across authentication, session handling, CSRF defense, role-based authorization, multi-tenant organization isolation, and transaction concurrency.

All security controls were tested against live PostgreSQL transactions and automated regression test suites without weakening any security constraints for testing convenience.

---

## 2. Authentication & Session Security

- **Session-Based Authentication**: NeighborNet AI utilizes Django's hardened session framework over stateless bearer tokens to prevent token leakage in browser storage and enable instantaneous server-side session revocation.
- **Session ID Regeneration**: Upon successful login, the existing session ID is rotated (`request.session.cycle_key()`) to defend against session fixation attacks.
- **Session Expiration**: Inactive sessions expire after 2 hours (`SESSION_COOKIE_AGE = 7200`). Sensitive operations require active session validation.
- **Password Hashing**: Passwords stored using PBKDF2 with SHA-256 (390,000+ iterations default in Django 6.1).

---

## 3. CSRF Protection Architecture

- **Django CSRF Middleware**: Active on all state-changing endpoints (`POST`, `PUT`, `PATCH`, `DELETE`).
- **Token Verification**: Frontend Axios / Fetch client retrieves the CSRF token from `/api/v1/accounts/csrf/` and injects it into every mutation request via the `X-CSRFToken` HTTP header.
- **Strict Verification in Tests**: End-to-end integration tests enforce CSRF validation (`enforce_csrf_checks=True`), confirming unauthorized or un-tokened mutations are rejected with HTTP 403.

---

## 4. Role-Based Access Control & Multi-Role Permissions

NeighborNet AI implements granular role-based access control (RBAC):
- `FOOD_PROVIDER`: Can create, update, and withdraw own surplus food listings. Cannot approve allocations or modify disaster states.
- `RECIPIENT`: Can register shelter demand requests and confirm receipts. Cannot access other organizations' draft listings.
- `VOLUNTEER`: Can view assigned delivery tasks, submit location pings, and complete deliveries. Cannot view other volunteers' personal telephone numbers or home addresses.
- `COORDINATOR`: Can generate optimization runs, approve allocations, activate/resolve disaster modes, and manage user verifications.

### Multi-Role Boundary Isolation:
Users holding multiple approved roles (e.g. Volunteer Courier + Provider Staff) operate within strict permission contexts:
- A user cannot approve their own provider listing as a coordinator.
- Cross-organization mutation is blocked by `OrganizationMembership` validation.

---

## 5. Organization Multi-Tenant Isolation

Organizations (kitchens, NGOs, shelters) are strictly isolated:
- Food listings and resource requests query filters restrict access to `organization_id` matching active user memberships.
- Attempts to mutate an external organization's resource listing via direct ID manipulation return `403 Forbidden` or `404 Not Found`.

---

## 6. Atomic Concurrency & Negative Inventory Prevention

To eliminate race conditions during high-volume disaster relief or simultaneous community claims:
1. **Database Row Locks (`select_for_update`)**: When an allocation recommendation is reviewed and approved, the corresponding `FoodListing` record is locked within an atomic transaction:
   ```python
   with transaction.atomic():
       listing = FoodListing.objects.select_for_update().get(id=listing_id)
       if listing.remaining_quantity < requested_quantity:
           raise InsufficientInventoryError("Requested quantity exceeds available stock.")
       listing.remaining_quantity -= requested_quantity
       listing.save()
   ```
2. **Negative Inventory Constraint**: PostgreSQL `CheckConstraint` enforces `remaining_quantity >= 0` at the database level, ensuring impossible overselling even in cases of unexpected application faults.

---

## 7. Restricted Access to Volunteer PII

- Personal Identifiable Information (PII) including volunteer home address coordinates, national identity numbers, and driver license images are strictly restricted to system coordinators.
- Provider and recipient interfaces receive only the volunteer's first name, vehicle type, and active delivery task status.

---

## 8. Production Settings Configuration Audit

The production configuration in `backend/config/settings/production.py` enforces the following security directives:

```python
DEBUG = False
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')

# Cookie Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Allows frontend to read token for X-CSRFToken header
CSRF_COOKIE_SAMESITE = 'Lax'

# HTTP Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year HSTS
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## 9. Security Audit Outcome

| Test Area | Result | Status |
|---|:---:|:---:|
| Session Authentication & Expiry | Verified | PASS |
| CSRF Header Defense | Verified | PASS |
| Role & Multi-Role Isolation | Verified | PASS |
| Organization Boundary Isolation | Verified | PASS |
| Coordinator Disaster Activation Lock | Verified | PASS |
| Concurrent Inventory Contention | Verified | PASS |
| Negative Stock Prevention | Verified | PASS |
| Production Flags (`DEBUG=False`) | Verified | PASS |
