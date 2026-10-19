# NeighborNet AI — Advanced Evaluation Methodology (`MODELX_EVAL_ADVANCED_V1`)

**Suite Code:** `MODELX_EVAL_ADVANCED_V1`  
**Purpose:** Deterministic stress test optimization evaluation suite for ModelX 2.0 competition  
**Implementation:** `backend/apps/intelligence/fixtures/advanced_scenarios.py`

---

## 1. Evaluation Methodology & Hard Constraints

All algorithms evaluated in `MODELX_EVAL_ADVANCED_V1` operate under identical hard constraints:
1. **Donor Category Compatibility:** Surplus item category must match request item category.
2. **Food Safety Expiry Buffer:** Expiry time must exceed delivery time + 2 hours buffer (`safe_until > target_time + 2h`).
3. **Provider Verification:** Unverified food providers are strictly excluded.
4. **Courier Carrying Capacity:** Total allocated weight per courier cannot exceed maximum vehicle capacity (kg).
5. **Courier Shift Window:** Pickup/delivery must fall within courier available shift window.
6. **Unit Separation:** Allocations are evaluated in isolated unit domains (`kg`, `L`, `kits`); cross-unit operations or incompatible units are rejected.

---

## 2. Description of 7 Stress-Test Scenarios

### Scenario 1: Competing Food Expiry Deadlines
- **Description:** 5 surplus lots with overlapping tight expiry windows (2h to 6h) competing for 3 NGO recipient requests with varying urgencies.
- **Challenge:** Evaluates solver's ability to prioritize short-expiry lots before food spoils.

### Scenario 2: Insufficient Volunteer Carrying Capacity
- **Description:** 200 kg total surplus supply across 4 lots, but courier vehicle capacity is capped at 100 kg total across 2 active volunteers.
- **Challenge:** Tests partial allocation efficiency and vehicle capacity constraint enforcement.

### Scenario 3: Overlapping Pickup & Delivery Schedules
- **Description:** 4 donor pickup windows restricted to 10:00–12:00, competing with recipient shelter lunch service times (11:30–12:30).
- **Challenge:** Tests temporal window feasibility screening and schedule conflict resolution.

### Scenario 4: Uneven Multi-Tier Recipient Priority Weights
- **Description:** High-volume low-priority requests (Standard, 100 kg) vs low-volume critical priority requests (Orphanage/Critical, 20 kg).
- **Challenge:** Verifies solver objective function weights high priority over sheer weight volume.

### Scenario 5: Disaster Resource Scarcity & Road Restrictions
- **Description:** Emergency flood relief mode in Moratuwa with 50% supply deficit and simulated road hazard blockages.
- **Challenge:** Evaluates disaster prioritization and spatial routing around restricted road segments.

### Scenario 6: Volunteer Cancellation & Disruption Recovery
- **Description:** Primary courier assigned to 50 kg delivery becomes unavailable en route.
- **Challenge:** Evaluates atomic replanning, replacement courier reassignment, and state consistency.

### Scenario 7: Mixed Kilograms, Liters & Emergency Kit Isolation
- **Description:** Supply lots containing 100 kg rice, 50 L drinking water, 20 emergency kits, and 10 invalid `boxes`.
- **Challenge:** Enforces unit isolation rules and rejects non-standard unit types without cross-unit summing.

---

## 3. Evaluated Algorithms

1. **First-Come First-Served (FCFS Baseline):** Sequential chronological matching based on creation order.
2. **Nearest Compatible (Greedy Proximity Baseline):** Greedy matching based on minimum spatial distance.
3. **Google OR-Tools CP-SAT (Primary Solver):** Multi-objective Integer Programming solver modeling exact constraints and objective weights.

---

## 4. Execution & Reproducibility Command

To execute the suite and print detailed invariant reports:

```bash
python manage.py evaluate_advanced_scenarios
```
