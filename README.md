<<<<<<< HEAD
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
=======
# NeighborNet AI — Intelligent Food Rescue & Disaster Resource Coordination Platform

**NeighborNet AI** is a real-time, community-driven food rescue and disaster relief coordination platform engineered for the **ModelX 2.0** competition.

The platform bridges surplus food providers (restaurants, bakeries, supermarkets) with verified recipient organizations (NGOs, community kitchens, shelters) via volunteer couriers in **Normal Community Mode**, and dynamically transitions into high-priority emergency logistics during **Disaster Response Mode**.

---

## 1. Project Structure

```text
NeighborNet/
├── frontend/              # React 19 + Vite + TypeScript + Mantine UI + Tailwind CSS
│   ├── src/
│   │   ├── components/    # Reusable UI widgets, navigation, stats
│   │   ├── contexts/      # AuthContext, NotificationContext
│   │   ├── pages/         # Unified Dashboard, Explorer, Admin Command Center
│   │   ├── services/      # Typed API & mock service layer
│   │   └── types/         # TypeScript domain models
│   ├── Dockerfile
│   └── package.json
├── backend/               # Django 6 + Django REST Framework + PostgreSQL / PostGIS
│   ├── config/            # Django settings (base, dev, prod), URLs, WSGI, ASGI
│   ├── apps/
│   │   ├── accounts/      # Custom User, Multi-role approval, Auth & Dashboards
│   │   ├── organizations/ # Commercial & NGO entities, Coordinator verification
│   │   ├── resources/     # Surplus food & relief inventory
│   │   ├── requests/      # Requisitions with priority & disaster validation
│   │   ├── volunteers/    # Courier profiles, capacity & availability
│   │   ├── deliveries/    # Atomic allocations & delivery state machine
│   │   ├── disasters/     # Disaster declaration & emergency lifecycle
│   │   ├── notifications/ # Real-time alerts
│   │   └── audit/         # Immutable security & activity audit logs
│   ├── common/            # Custom DRF permissions, pagination, validators
│   ├── tests/             # Automated test suite (Pytest-Django)
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── docs/                  # Architecture, API specs, DB schema, Frontend mapping
│   ├── backend-architecture.md
│   ├── api-spec.md
│   ├── database-schema.md
│   └── frontend-api-mapping.md
├── docker-compose.yml     # Multi-container PostGIS + Backend + Frontend
├── PHASE2_PROGRESS.md     # Phase 2 implementation summary
└── README.md
>>>>>>> 485c297 (Initial commit - NeighborNet AI)
```

---

<<<<<<< HEAD
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
=======
## 2. Quick Start

### Option A: Run via Docker Compose (Recommended)
Launch the PostGIS database, Django backend, and React frontend with a single command:

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api/v1/`
- PostgreSQL/PostGIS: `localhost:5432`

---

### Option B: Run Locally

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment & install requirements
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run migrations & seed realistic demo data
python manage.py migrate
python manage.py seed_demo

# Start Django development server
python manage.py runserver 8000
```

#### 2. Frontend Setup
```bash
cd frontend

# Install npm packages
npm install

# Start Vite development server
npm run dev
```

Visit `http://localhost:5173`.

---

## 3. Demo Accounts & Credentials

The `seed_demo` command populates realistic Sri Lankan scenarios matching the frontend mock personas:

| Role | Account Email | Password | Persona & Capabilities |
|---|---|---|---|
| **Food Provider** | `fathima@pererahotels.lk` | `password123` | Fathima Rizwan (Perera Grand Catering & Hotel) — Surplus food listings |
| **Recipient NGO** | `sister.mary@graceeldercare.org` | `password123` | Sister Mary Teresa (Grace Home for the Elderly) — Daily requisitions |
| **Volunteer** | `dinesh.mendis@gmail.com` | `password123` | Dinesh Mendis — Motorcycle courier (25kg capacity), delivery claims |
| **Multi-Role** | `ravi.mendis@greenbites.lk` | `password123` | Ravi Mendis — Food Provider (GreenBites Bakery) + Volunteer Courier |
| **Coordinator / Admin** | `kaveen.j@dmc.gov.lk` | `password123` | Dr. Kaveen Jayawardena (DMC) — Disaster activation, org verification |
| **Recipient + Volunteer** | `anuki.b@suwasetha.org` | `password123` | Anuki Bandara (Suwasetha Child Dev Center) — Shelter requisitions & deliveries |
| **Coordinator + Volunteer**| `malik.farook@redcross.lk` | `password123` | Malik Farook (Sri Lanka Red Cross) — Emergency coordination & field courier |

---

## 4. Testing & Verification

Run the comprehensive automated backend test suite using `pytest`:

>>>>>>> 485c297 (Initial commit - NeighborNet AI)
```bash
pytest backend/tests -v
```

<<<<<<< HEAD
All 14 comprehensive tests covering auth, multi-role security, atomic allocations, state transitions, disaster rules, and dashboards run in ~16 seconds.

---

## Docker Deployment

To spin up PostgreSQL/PostGIS, Django backend, and the React frontend simultaneously:
```bash
docker compose up --build
```
=======
**Results**: 14 tests passing across authentication, multi-role permissions, atomic allocations, state machine validation, disaster boundaries, and unified dashboards.

---

## 5. Documentation Links

- [Backend Architecture](file:///docs/backend-architecture.md)
- [REST API Specification](file:///docs/api-spec.md)
- [Database Schema & ERD](file:///docs/database-schema.md)
- [Frontend-to-Backend Service Mapping](file:///docs/frontend-api-mapping.md)
- [Phase 2 Progress Report](file:///PHASE2_PROGRESS.md)
>>>>>>> 485c297 (Initial commit - NeighborNet AI)
