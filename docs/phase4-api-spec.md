# NeighborNet AI — Phase 4 Intelligence REST API Specification

All intelligence endpoints are versioned under `/api/v1/intelligence/` and require valid session or token authentication. Coordinator permissions are strictly enforced on state-changing endpoints.

---

## 1. Candidate Eligibility Screening
### `GET /api/v1/intelligence/matches/`
Returns all compatible candidate resource lots and recipient requests screened by hard constraints.

**Response `200 OK`:**
```json
{
  "count": 46,
  "matches": [
    {
      "resource_id": "97e61530-58fe-4a0b-a010-863a8276fce0",
      "resource_name": "Vegetable Roti & Curry Puffs Batch",
      "provider_name": "GreenBites Bakery & Cafe",
      "request_id": "060d4da1-77b3-4fec-be10-09a25b29f798",
      "request_item_name": "Hot Prepared Lunch Rations",
      "recipient_name": "Grace Home for the Elderly",
      "category": "prepared_meals",
      "available_quantity": 60.0,
      "remaining_quantity": 80.0,
      "compatible_quantity": 60.0,
      "unit": "meals",
      "distance_km": 1.71,
      "priority": "HIGH",
      "is_disaster_relief": false,
      "constraints_satisfied": [
        "Unexpired food shelf-life (use_by > now + 2h)",
        "Food safety handling guidelines complete",
        "Verified provider and recipient organizations",
        "Category compatibility matrix satisfied",
        "Straight-line distance within 35km service area",
        "Feasible collection and delivery time windows"
      ]
    }
  ]
}
```

---

## 2. Solver Execution & Optimization
### `POST /api/v1/intelligence/optimize/`
Executes mathematical resource optimization or baseline matching.

**Request Payload:**
```json
{
  "method": "ORTOOLS_CPSAT",
  "mode": "NORMAL",
  "time_limit_seconds": 10
}
```
*Options for `method`:* `ORTOOLS_CPSAT`, `BASELINE_FCFS`, `BASELINE_NEAREST`
*Options for `mode`:* `NORMAL`, `DISASTER`

**Response `201 Created`:**
```json
{
  "batch": {
    "id": "2dbd3f82-38b4-4e9f-860f-e2c7abfa7e1d",
    "mode": "NORMAL",
    "method": "ORTOOLS_CPSAT",
    "status": "PENDING_APPROVAL",
    "solver_status": "OPTIMAL",
    "runtime_ms": 146.85,
    "total_allocated_quantity": 265.0,
    "fulfilled_demand_pct": 9.8,
    "unmet_demand": 2435.0,
    "recommendationsCount": 7,
    "recommendations": [ ... ]
  }
}
```

---

## 3. Recommendation Batch Workflow
### `GET /api/v1/intelligence/recommendations/`
List recommendation batches with status filtering (`DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `APPLIED`).

### `POST /api/v1/intelligence/recommendations/{id}/approve/`
*(Coordinator Only)* Approves a pending recommendation batch.

### `POST /api/v1/intelligence/recommendations/{id}/reject/`
*(Coordinator Only)* Rejects a batch with a mandatory explanation reason.
```json
{ "reason": "Operational schedule conflict" }
```

### `POST /api/v1/intelligence/recommendations/{id}/apply/`
*(Coordinator Only)* Atomically locks resources via `select_for_update()`, creates verified `Allocation` records, and creates assigned `DeliveryTask` records.
**Response `200 OK`:**
```json
{
  "success": true,
  "batch_id": "2dbd3f82-38b4-4e9f-860f-e2c7abfa7e1d",
  "allocations_count": 7,
  "delivery_tasks_count": 7
}
```

---

## 4. Disruption Detection & Recovery
### `POST /api/v1/intelligence/recovery/preview/`
Reports an operational disruption and generates a recomputed replacement plan.
```json
{
  "task_id": "a92e1040-cfc3-4ad8-84ea-3610ec54ea12",
  "event_type": "VOLUNTEER_UNAVAILABLE",
  "details": "Courier vehicle breakdown en route"
}
```

### `POST /api/v1/intelligence/recovery/{disruption_id}/apply/`
*(Coordinator Only)* Atomically applies the proposed replacement plan.

---

## 5. Descriptive Analytics
### `GET /api/v1/intelligence/analytics/`
Returns Pandas/NumPy aggregated real-time metrics for inventory, demand, logistics, fleet, and disaster status.
