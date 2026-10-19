# NeighborNet AI — Intelligence Architecture Specification

## 1. Architectural Philosophy
NeighborNet AI Phase 4 implements an in-process, modular intelligence engine within the monolithic Django backend. It rejects brittle external microservices, paid cloud APIs, and black-box LLM decision-makers in favor of deterministic constraint satisfaction and mathematical optimization.

```
+-----------------------------------------------------------------------------------+
|                            Coordinator Workspace (React)                          |
|  - Candidate Matrix  - Solver Controls  - Approval Diff  - Recovery  - Analytics  |
+-----------------------------------------+-----------------------------------------+
                                          | REST API (Token Auth + DRF)
+-----------------------------------------v-----------------------------------------+
|                         Django Intelligence App (backend/apps/intelligence)       |
|                                                                                   |
|  +------------------------+  +------------------------+  +---------------------+  |
|  |  Eligibility Screening |  |   Baselines (FCFS /    |  |  Google OR-Tools    |  |
|  |   - Safety validation  |  |        Nearest)        |  |  CP-SAT Optimizer   |  |
|  |   - Category matrix    |  +------------------------+  |  - Scaled Integer   |  |
|  |   - Distance filtering |                              |  - Multi-criteria   |  |
|  +-----------+------------+                              +----------+----------+  |
|              |                                                      |             |
|              +--------------------------+---------------------------+             |
|                                         |                                         |
|                       +-----------------v-----------------+                       |
|                       |  Volunteer Logistics Feasibility  |                       |
|                       |   - Courier capacity check        |                       |
|                       |   - Sector proximity staging      |                       |
|                       +-----------------+-----------------+                       |
|                                         |                                         |
|                       +-----------------v-----------------+                       |
|                       |  Coordinator Approval Workflow    |                       |
|                       |   DRAFT -> PENDING -> APPROVED    |                       |
|                       |   - Atomic row locks              |                       |
|                       |   - Allocation & Task creation    |                       |
|                       +-----------------+-----------------+                       |
|                                         |                                         |
|                       +-----------------v-----------------+                       |
|                       |  Disruption Detection & Recovery  |                       |
|                       |   - Recomputed replacement plan   |                       |
|                       +-----------------------------------+                       |
+-----------------------------------------+-----------------------------------------+
                                          |
                               +----------v-----------+
                               | PostgreSQL + PostGIS |
                               +----------------------+
```

---

## 2. Directory & Component Layout
- `backend/apps/intelligence/`:
  - `models.py`: `RecommendationBatch`, `OptimizationRecommendation`, `DisruptionEvent`, `EvaluationMetricRun`.
  - `views.py`: REST endpoints for screening, solver execution, batch lifecycle, recovery preview/apply, analytics, evaluations.
  - `serializers.py`: DRF serializers for inputs and rich outputs.
  - `permissions.py`: `IsCoordinatorOnly` guards sensitive allocation approvals.
  - `services/`:
    - `eligibility.py`: Deterministic hard constraint checks.
    - `distance.py`: Spatial proximity engine with Haversine great-circle calculation labeled explicitly as `straight_line_haversine`.
    - `baseline_matching.py`: Baseline A (FCFS) & Baseline B (Nearest Compatible).
    - `optimizer.py`: Google OR-Tools CP-SAT formulation with integer scaling $S=100$.
    - `volunteer_assignment.py`: Two-stage logistics validation and courier vehicle capacity matching.
    - `disaster_priority.py`: Emergency shortage breakdown, priority weighting, and life-sustaining supply matching.
    - `explainability.py`: Constraint-grounded deterministic rationale generation.
    - `approval.py`: Coordinator batch approval, rejection, and atomic execution with PostgreSQL `select_for_update()`.
    - `recovery.py`: Disruption incident tracking and replacement replanning.
    - `analytics.py`: Pandas and NumPy data aggregation on real PostgreSQL records.
  - `management/commands/evaluate_intelligence.py`: CLI benchmark runner comparing algorithms across identical test scenarios.

---

## 3. Two-Stage Decision Model
1. **Stage 1: Multi-Criteria Resource Allocation**
   - Evaluates eligible donors and recipients to determine optimal quantities $x_{i,j}$.
   - Solves supply-demand matching without being artificially constrained by temporary courier availability.
2. **Stage 2: Logistics Feasibility & Courier Staging**
   - For each allocated lot $(i, j)$ with weight $Q_{alloc}$, queries active and available volunteers within the sector.
   - Evaluates:
     $$V.vehicle\_capacity\_kg \ge Q_{alloc}$$
   - Assigns closest qualified courier; marks unassigned lots with clear logistics warnings so coordinators are never misled.

---

## 4. Concurrency & Transactional Safety
When a Coordinator executes "Apply Batch", the system:
1. Wraps execution in `transaction.atomic()`.
2. Obtains row-level locks via `Resource.objects.select_for_update().get(id=r_id)`.
3. Verifies that `resource.available_quantity >= allocated_qty`.
4. Obtains row-level locks on `ResourceRequest.objects.select_for_update().get(id=req_id)` and verifies `remaining_quantity >= allocated_qty`.
5. Creates real `Allocation` records and transitions `RecommendationBatch.status = 'APPLIED'`.
6. Creates corresponding `DeliveryTask` records assigned to the staged volunteer.
7. If any resource shifted or became unavailable between recommendation and application, the transaction aborts with a 409 Conflict error.
