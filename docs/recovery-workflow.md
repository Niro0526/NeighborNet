# NeighborNet AI — Disruption Detection & Recovery Replanning Workflow

## 1. Disruption Taxonomy

Operational disruptions occur in dynamic community food rescue and disaster relief logistics. NeighborNet AI tracks the following disruption events:

| Event Type Code | Cause | Immediate System Action |
|---|---|---|
| `VOLUNTEER_UNAVAILABLE` | Assigned courier uncontactable or vehicle failure. | Disassociates courier, marks task status `DISRUPTED`, triggers Stage 2 courier replanning. |
| `VOLUNTEER_CANCELLED` | Volunteer submits emergency withdrawal before pickup. | Reverts task status to `DISRUPTED`, stages nearest available replacement courier. |
| `RESOURCE_WITHDRAWN` | Donor reports food spoiled, damaged, or recalled. | Revokes affected allocation, releases remaining request demand for re-optimization. |
| `RESOURCE_EXPIRED` | Shelf life elapsed prior to collection. | Flags resource as `EXPIRED`, cancels delivery task, audits reason. |
| `PICKUP_DELAY` | Facility closed or collection window missed. | Reschedules pickup window or reallocates to alternative recipient. |
| `DELIVERY_FAILURE` | Recipient shelter closed or unreachable. | Flags delivery failure, redirects courier to nearest alternative community shelter. |
| `ROAD_RESTRICTION` | Flooding, police barricade, or hazard zone obstruction. | Recalculates route avoidance and rechecks courier vehicle capability. |

---

## 2. Recovery Lifecycle & State Transition

```
Active Delivery Task
         │
         ▼
[Disruption Reported] ───> DisruptionEvent Created in DB
         │
         ▼
[Recovery Preview] ──────> 1. Preserve Completed & Unaffected Deliveries
                           2. Query Available Standby Couriers with Capacity >= Qty
                           3. Compute Side-by-Side Diff Plan
         │
         ▼
[Coordinator Review] ────> Coordinator Inspects Rationale & Capacity Checks
         │
         ├─── Rejection ──> Manual Handling / Coordinator Override
         │
         └─── Approval ───> Atomic PostgreSQL Transaction:
                            - Task Status Updated / Reassigned
                            - Allocation Integrity Verified
                            - Audit Log Emitted
```

---

## 3. Atomic Replacement Guarantees

1. **Preservation of Completed Deliveries:** Completed tasks (`DELIVERED`) are never altered or reversed.
2. **Partial Replanning:** Only disrupted uncompleted tasks are re-evaluated; unaffected delivery tasks continue without disruption.
3. **Atomic Execution:** Replacement volunteers and reassignments are applied inside `transaction.atomic()`, ensuring no partial or corrupted states occur if a database conflict arises.
