# NeighborNet AI — Backend (Phase 2)

NeighborNet AI is an intelligent community food rescue and disaster resource coordination platform built for the ModelX 2.0 competition.

This backend provides a robust **Django 6 + Django REST Framework** foundation backed by **PostgreSQL / PostGIS**, featuring HttpOnly session authentication, multi-role permissions, atomic inventory reservation, volunteer lifecycle tracking, and dual Normal / Disaster operating modes.

---

## Architecture Highlights

1. **Authentication & Session Security**:
   - Django session-based authentication with `HttpOnly`, `SameSite=Lax`, and CSRF protection.
   - Credentials and tokens are **never** stored in browser `localStorage`.
   - Dedicated `/api/v1/auth/csrf/` endpoint provides initial CSRF handshake token.

2. **Multi-Role Permissions**:
   - Custom `User` model with separate approved platform roles (`FOOD_PROVIDER`, `RECIPIENT`, `VOLUNTEER`, `COORDINATOR`).
   - One user can hold multiple roles simultaneously (e.g. `FOOD_PROVIDER` + `VOLUNTEER`) without identity switching.
   - Client self-assignment of `COORDINATOR` role is strictly rejected.

3. **Atomic Allocations & Delivery Lifecycle**:
   - `select_for_update()` database row-level locking ensures zero over-allocation or negative inventory under concurrent load.
   - Strict delivery state machine: `AVAILABLE` → `ACCEPTED` → `ARRIVED_PICKUP` → `PICKED_UP` → `ARRIVED_DELIVERY` → `DELIVERED`.

4. **Dual Operating Modes**:
   - **Normal Community Mode**: Food surplus matching, pantry rescue, bakery items.
   - **Disaster Response Mode**: Emergency requisitioning of food, drinking water, and relief supplies referencing active disaster events.
   - Only approved Coordinators can declare, activate, or resolve disaster events.

5. **Unified Dashboard Endpoint**:
   - `GET /api/v1/dashboard/me/`: Introspects the authenticated user's approved roles and dynamically combines operational modules into a single response.
   - `GET /api/v1/dashboard/admin/`: Restricted to approved Coordinators, returning active disaster state, verification queues, and audit summaries.

---

## Directory Structure

```text
backend/
├── config/
│   ├── settings/
│   │   ├── base.py           # Shared settings, apps, DRF, dual GIS config
│   │   ├── development.py    # Local settings
│   │   └── production.py     # Production settings with HTTPS enforcement
│   ├── urls.py               # Root API routing (/api/v1/)
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── accounts/             # Custom User, Multi-role assignments, Auth & Dashboard views
│   ├── organizations/        # Business & NGO profiles, Coordinator verification
│   ├── resources/            # Surplus food & relief supplies inventory
│   ├── requests/             # Recipient requisitioning & disaster validation
│   ├── volunteers/           # Courier profiles, availability, capacity
│   ├── deliveries/           # Allocations & delivery state machine
│   ├── disasters/            # Disaster lifecycle & emergency management
│   ├── notifications/        # User notifications & alert triggers
│   └── audit/                # Immutable activity & security audit logging
├── common/                   # Reusable permissions, pagination, validators
├── tests/                    # Pytest test suite (14 passing tests)
├── manage.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Getting Started

### 1. Prerequisites
- Python 3.12+ (tested on Python 3.12 and 3.13)
- PostgreSQL 16+ (with PostGIS extension enabled or PostGIS Docker container)

### 2. Environment Configuration
Copy the example environment file and adjust your database credentials:
```bash
cp .env.example .env
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Seed Demo Data
Populate realistic Sri Lankan demo scenarios matching the frontend mock personas:
```bash
python manage.py seed_demo
```

This creates:
- `fathima@pererahotels.lk` (Food Provider — Perera Grand Catering & Hotel)
- `sister.mary@graceeldercare.org` (Recipient NGO — Grace Home for the Elderly)
- `dinesh.mendis@gmail.com` (Volunteer Courier — Motorbike, 25kg capacity)
- `ravi.mendis@greenbites.lk` (Dual-Role: Food Provider + Volunteer Courier)
- `kaveen.j@dmc.gov.lk` (Coordinator / Admin — Disaster Management Center)
- `anuki.b@suwasetha.org` (Recipient + Volunteer Courier)
- `malik.farook@redcross.lk` (Coordinator + Volunteer Courier)
- Default password for all demo accounts: `password123`

### 6. Start the Server
```bash
python manage.py runserver 8000
```
Server runs at `http://localhost:8000`.

---

## Running Automated Tests

Run the full pytest suite with pytest-django:
```bash
pytest backend/tests -v
```

All 14 comprehensive tests covering auth, multi-role security, atomic allocations, state transitions, disaster rules, and dashboards run in ~16 seconds.

---

## Docker Deployment

To spin up PostgreSQL/PostGIS, Django backend, and the React frontend simultaneously:
```bash
docker compose up --build
```
