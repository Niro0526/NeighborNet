# NeighborNet AI — Optimization Model Specification

## 1. Mathematical Formulation (CP-SAT)

The core allocation engine formulates resource redistribution as an integer-scaled Constraint Satisfaction & Optimization Problem (COP) solved via Google OR-Tools CP-SAT.

### Decision Variables
Let $I$ be the set of eligible available resources, and $J$ be the set of compatible verified requests.
For each compatible pair $(i, j) \in I \times J$:

$$x_{i, j} \in \mathbb{Z}_{\ge 0}, \quad 0 \le x_{i, j} \le \min(\lfloor S \cdot Supply_i \rfloor, \lfloor S \cdot Demand_j \rfloor)$$

Where:
- $S = 100$ is the integer scale factor, allowing two decimal places of continuous quantity precision (e.g. 12.75 kg = 1,275 scaled units).
- $Supply_i$: Available unallocated quantity of resource $i$.
- $Demand_j$: Remaining unfulfilled demand of request $j$.

---

## 2. Hard Constraints

### 1. Resource Capacity Limit
Total allocated quantity from any resource $i$ cannot exceed its available physical supply:

$$\sum_{j \in J} x_{i, j} \le \lfloor S \cdot Supply_i \rfloor \quad \forall i \in I$$

### 2. Request Demand Upper Bound
Total allocated quantity to any recipient $j$ cannot exceed its recorded remaining demand:

$$\sum_{i \in I} x_{i, j} \le \lfloor S \cdot Demand_j \rfloor \quad \forall j \in J$$

### 3. Unit & Category Eligibility Isolation
$$x_{i, j} = 0 \quad \text{if Pair } (i, j) \text{ fails eligibility (Unit mismatch, Expired, Unverified, Out of zone)}$$

### 4. Non-Negativity & Integrality
$$x_{i, j} \ge 0, \quad x_{i, j} \in \mathbb{Z} \quad \forall i, j$$

---

## 3. Multi-Criteria Objective Function

The objective maximizes community utility while prioritizing urgent/disaster demand, preventing perishable food waste, and reducing travel distance:

$$\max \sum_{(i, j) \in I \times J} x_{i, j} \cdot C_{i, j}$$

Where unit coefficient $C_{i, j}$ is calculated as:

$$C_{i, j} = 1000 + R_{priority}(j) + R_{disaster}(j) + R_{expiry}(i) - P_{distance}(i, j)$$

### Parameter Definitions:
1. **Base Demand Fulfillment Reward ($1000 \cdot x_{i,j}$):**
   - Ensures maximizing total allocated demand ($\sum x_{i,j}$) is the primary mathematical priority.
2. **Priority Coverage Bonus ($R_{priority}$):**
   - `URGENT`: $+500$
   - `HIGH`: $+300$
   - `MEDIUM`: $+100$
   - `LOW`: $+0$
3. **Disaster Relief Bonus ($R_{disaster}$):**
   - Disaster relief requests: $+400$
4. **Expiry Prevention Bonus ($R_{expiry}$):**
   - Remaining shelf life $\le 6\text{h}$: $+400$
   - Remaining shelf life $\le 18\text{h}$: $+250$
   - Remaining shelf life $\le 36\text{h}$: $+100$
5. **Distance Burden Penalty ($P_{distance}$):**
   - $P_{distance} = \text{round}(5 \cdot Dist_{km})$. Subtracts 5 points per km to break ties in favor of local community distribution.

---

## 4. Solver Output & Performance Guarantees

- **Time Limit:** Configurable default of 10.0 seconds.
- **Status Returns:** `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, or `MODEL_INVALID`.
- **Honest Feasibility:** If no candidate passes hard constraints, the solver honestly returns status `INFEASIBLE` with empty recommendations.
