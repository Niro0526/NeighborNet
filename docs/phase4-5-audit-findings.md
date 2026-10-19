# NeighborNet AI — Phase 4.5 Audit Findings & Quality Verification

## Executive Summary
This document records the independent audit findings for Phase 4 of NeighborNet AI, covering backend intelligence services, optimization formulation, evaluation reproducibility, food safety rules, volunteer logistics, and frontend benchmark metrics.

---

## 1. Audit Classifications

### A. Confirmed Defects & Implementation Gaps
1. **Unit Mismatch Vulnerability in Eligibility Screening:**
   - *Finding:* `evaluate_resource_request_eligibility()` checked category compatibility but failed to enforce strict unit equality (`resource.unit == request.unit`).
   - *Impact:* Potential cross-unit quantity aggregation (e.g. summing discrete `boxes` and `kg` into a single total).
   - *Correction:* Enforce strict unit isolation in `eligibility.py`. If `resource.unit != request.unit`, mark candidate pair ineligible.

2. **Non-Deterministic Benchmark Execution:**
   - *Finding:* `evaluate_intelligence.py` executed queries against dynamic live database state using `now = timezone.now()`.
   - *Impact:* Expiry status and available inventory shifted over time, producing non-reproducible evaluation outputs (e.g. returning 0.0 allocations after live records were consumed).
   - *Correction:* Implement a frozen benchmark dataset fixture with fixed timestamps (`EVALUATION_REFERENCE_TIMESTAMP`), fixed random seeds, and immutable snapshot records.

3. **Objective Function Documentation Inconsistency:**
   - *Finding:* `docs/optimization-model.md` listed $U(i,j) = 100 \times Priority(j) + 10 \times \max(0, 24 - HoursToExpiry(i)) - 5 \times Distance(i,j)$, omitting the primary demand fulfillment coefficient ($1000 \cdot x_{i,j}$).
   - *Impact:* Documentation suggested tie-breakers could override total demand fulfillment.
   - *Correction:* Update documentation to explicitly document the full multi-criteria objective formulation in `optimizer.py`.

4. **Safety Buffer Inconsistency:**
   - *Finding:* `eligibility.py` evaluated `safe_until <= now` (0-hour buffer) whereas specifications required a conservative 2-hour minimum transit/handling window (`safe_until <= now + 2h`).
   - *Impact:* Perishables expiring within <2 hours could be recommended for pickup even if transit time made safe consumption impossible.
   - *Correction:* Enforce `safe_until > now + timedelta(hours=2)` in `eligibility.py`.

5. **Fulfillment Metric Ambiguity:**
   - *Finding:* Benchmark reports conflated Quantity-Weighted Fulfillment % with Request-Level Fulfillment % without reporting fully served, partially served, and unserved request counts.
   - *Impact:* Ambiguity in evaluation interpretations.
   - *Correction:* Compute and report both Quantity Fulfillment % and Request Fulfillment % alongside exact counts of fully satisfied, partially satisfied, and unserved requests.

---

### B. Potential Risks Requiring Regression Tests
1. **Integer Scaling Boundaries ($S=100$):** Very small quantities (e.g. 0.01 kg, 0.05 kg) must be accurately preserved without zero-rounding or float overflow.
2. **Volunteer Schedule Overlaps:** A volunteer courier already assigned to an active delivery must not be assigned to an overlapping delivery task window.
3. **Stale Plan Rejection:** Simultaneous batch applications must be protected against race conditions using PostgreSQL `select_for_update()` row locks.
4. **Disruption Replanning:** Disruption recovery must preserve completed deliveries while safely reassigning disrupted tasks.

---

### C. Verified Correct Behavior
1. **OR-Tools Solver Formulation:** Integer scaling $S=100$ accurately enforces conservation of inventory ($\sum x \le Supply$, $\sum x \le Demand$).
2. **Geospatial Distance Calculations:** Haversine distance correctly enforces the 35 km Moratuwa/Colombo South service area boundary.
3. **Database Concurrency & Security:** `select_for_update()` row-level locks prevent over-allocation during atomic batch application.
4. **Coordinator Workspace & REST APIs:** Role-based permissions strictly limit allocation approvals to authorized Coordinators (`IsCoordinatorOnly`).
