# NeighborNet AI — Database Verification & Engine Architecture (Phase 5)

## 1. Engine & Extension Verification

NeighborNet AI operates on **PostgreSQL with PostGIS** spatial extensions. The backend settings strictly configure:

```python
# backend/config/settings/base.py
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME', 'neighbornet_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}
```

### PostGIS Capabilities Active:
- **Spatial Indexing**: GiST indexes on spatial coordinates (`PointField` in PostGIS) for food listings, shelter requests, and active volunteer couriers.
- **Geographic Distance Calculations**: Haversine and spheroidal distance computations (`ST_Distance`, `ST_DWithin`) used by Google OR-Tools optimization engine to compute realistic transport routing matrices across Colombo and Moratuwa sectors.
- **Disaster Hazard Zones**: Polygon geometry checks (`ST_Contains`, `ST_Intersects`) determining whether shelters or food providers fall within active disaster perimeter inundation/landslide zones.

---

## 2. Mock Dependency Removal in API Mode

In Phase 5, all production-facing frontend components and services were audited to ensure zero silent mock fallback when `VITE_DATA_SOURCE=api`.

### Frontend Service Audit Matrix:
| Service | API Endpoint | Mock Fallback Status | Data Persistence |
|---|---|---|---|
| `authService` | `/api/v1/accounts/me/`, `/login/`, `/logout/` | Strict API — throws on error | Server-side Django session + CSRF cookie |
| `foodService` | `/api/v1/food-listings/` | Strict API — throws on error | Live PostgreSQL `food_listings` table |
| `requestService` | `/api/v1/requests/` | Strict API — throws on error | Live PostgreSQL `food_requests` table |
| `allocationService` | `/api/v1/allocations/`, `/intelligence/recommendations/` | Strict API — throws on error | Live PostgreSQL `allocations` & `recommendation_batches` |
| `deliveryService` | `/api/v1/deliveries/` | Strict API — throws on error | Live PostgreSQL `delivery_tasks` & tracking logs |
| `volunteerService` | `/api/v1/volunteers/` | Strict API — throws on error | Live PostgreSQL `volunteers` profile table |
| `disasterService` | `/api/v1/disasters/` | Strict API — throws on error | Live PostgreSQL `disasters` & hazard zones |
| `analyticsService` | `/api/v1/analytics/overview/` | Strict API — returns error state | Derived entirely from live PostgreSQL records |

### Dashboard Hardcoded Fallbacks Removed:
1. **Coordinator Dashboard** (`CoordinatorDashboard.tsx`):
   - Removed artificial fallbacks (`|| 1240`, `|| 28`, `|| 54`, `|| 36`).
   - Sourced pending recommendation batches from live `/intelligence/recommendations/` endpoint.
   - Sourced pending allocations and emergency requests directly from API services.
2. **Food Provider Dashboard** (`ProviderDashboard.tsx`):
   - Removed hardcoded metrics (`|| 120`, `|| 12`, `|| 2`, `value="1"`).
   - Replaced static `ORG-001` query with live `/food-listings/` filtered by authenticated user organization.
   - Added explicit empty state rendering when zero listings exist.
3. **Recipient Dashboard** (`RecipientDashboard.tsx`):
   - Removed mock metrics (`|| 5`, `|| 3`, `"120 kg"`, `|| 8`).
   - Fulfilled quantities dynamically computed by summing live request allocations.
4. **Volunteer Dashboard** (`VolunteerDashboard.tsx`):
   - Removed `VOL-001` fallback in API mode; queries live volunteer profile via `/volunteers/me/`.
   - Removed hardcoded fallback hours (`|| 48`) and rating (`|| 4.9`).
5. **Global Navigation Header** (`Header.tsx`):
   - Added `isApiMode()` badge indicator: `[Database: PostgreSQL (Live API)]`.
   - Hidden "Reset All Demo Data" button when running in API mode to prevent accidental local state confusion.

---

## 3. Demo Seeding Guardrails

The demo seeding command (`backend/apps/accounts/management/commands/seed_demo.py`) was verified for production safety:
- **Production Guard**: Contains an immediate hard check:
  ```python
  if not settings.DEBUG and not options.get('force'):
      self.stdout.write(self.style.ERROR(
          'Safety check: seed_demo command is disabled in production environments (DEBUG=False).'
      ))
      return
  ```
- **Idempotency**: All demo records (users, organizations, disaster scenarios, food listings) use `update_or_create` or unique slug lookups, ensuring safe execution without duplicate primary key collisions.

---

## 4. Separation of Public Sri Lankan Evidence vs. Synthetic Operational Data

NeighborNet AI strictly maintains architectural separation between real-world reference datasets and application transactions:

1. **Public Sri Lankan Evidence (`data/evidence/`, `data/external/`)**:
   - Hector Kobbekaduwa Agrarian Research and Training Institute (HARTI) Colombo food price & wholesale bulletins.
   - Disaster Management Centre (DMC) Sri Lanka Situation Reports (Kelani River basin flooding).
   - Department of Census and Statistics (DCS) Poverty & Vulnerability Indicators.
   - Used strictly for baseline calorie valuation, geo-spatial bounds, hazard buffer zones, and demand estimation.
2. **Synthetic Benchmark Fixtures (`backend/fixtures/benchmarks/`)**:
   - 7 advanced operational stress-test scenarios (Phase 4.5/4.6) evaluated under Google OR-Tools CP-SAT solver.
   - Explicitly marked with `data_classification: "SYNTHETIC_BENCHMARK"`.
3. **Transactional PostgreSQL Database (`neighbornet_db`)**:
   - Contains live user accounts, sessions, organization memberships, live food listings, real-time allocations, and delivery tracking.
   - Never mixed with synthetic benchmark result claims.
