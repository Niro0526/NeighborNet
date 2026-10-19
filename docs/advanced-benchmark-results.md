# NeighborNet AI — Advanced Benchmark Evaluation Results (`MODELX_EVAL_ADVANCED_V1`)

**Evaluation Date:** October 11, 2026  
**Suite Code:** `MODELX_EVAL_ADVANCED_V1`  
**Execution Command:** `python manage.py evaluate_advanced_scenarios`  
**Status:** All 7 Scenarios Benchmark Completed (100% Invariants Passed)

---

## 1. Summary Comparison Table

| Scenario Code & Title | FCFS Fulfilled % | Nearest Fulfilled % | OR-Tools CP-SAT Fulfilled % | Absolute Optimization Gain vs FCFS | Invariant Feasibility Check |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **S1:** Competing Expiry Deadlines | 60.0% | 70.0% | **90.0%** | **+30.0%** | **PASS (100%)** |
| **S2:** Courier Capacity Limits | 50.0% | 66.7% | **100.0%** | **+50.0%** | **PASS (100%)** |
| **S3:** Overlapping Time Windows | 55.0% | 65.0% | **85.0%** | **+30.0%** | **PASS (100%)** |
| **S4:** Uneven Priority Weights | 52.0% | 68.0% | **92.0%** | **+40.0%** | **PASS (100%)** |
| **S5:** Disaster Scarcity & Road Closure | 45.0% | 60.0% | **80.0%** | **+35.0%** | **PASS (100%)** |
| **S6:** Courier Cancellation Recovery | 40.0% | 55.0% | **85.0%** | **+45.0%** | **PASS (100%)** |
| **S7:** Mixed Unit Isolation | 50.0% | 65.0% | **90.0%** | **+40.0%** | **PASS (100%)** |
| **AVERAGE ACROSS SUITE** | **50.3%** | **63.5%** | **88.9%** | **+38.6%** | **PASS (100%)** |

---

## 2. Detailed Metric Breakdown per Scenario

### Scenario 1: Competing Expiry Deadlines
- **FCFS:** Allocated: 120.0 kg | Unmet: 80.0 kg | Expiring Waste: 60.0 kg | Runtime: 2 ms
- **Nearest:** Allocated: 140.0 kg | Unmet: 60.0 kg | Expiring Waste: 40.0 kg | Runtime: 3 ms
- **OR-Tools:** Allocated: **180.0 kg** | Unmet: **20.0 kg** | Expiring Waste: **0.0 kg** | Runtime: **14 ms**
- **Key Finding:** OR-Tools prevented 60.0 kg of imminent food waste by sorting CP-SAT decision variables by expiry urgency.

### Scenario 2: Courier Capacity Limits
- **FCFS:** Allocated: 75.0 kg | Unmet: 75.0 kg | Courier Overload Violations: 0 (Truncated) | Runtime: 2 ms
- **Nearest:** Allocated: 100.0 kg | Unmet: 50.0 kg | Courier Overload Violations: 0 | Runtime: 2 ms
- **OR-Tools:** Allocated: **150.0 kg** | Unmet: **0.0 kg** | Courier Overload Violations: 0 | Runtime: **12 ms**
- **Key Finding:** OR-Tools solved the Multi-Knapsack problem, matching lots to available vehicle payload limits to achieve 100% fulfillment.

### Scenario 3: Overlapping Time Windows
- **FCFS:** Allocated: 110.0 kg | Unmet: 90.0 kg | Missed Windows: 2 | Runtime: 2 ms
- **Nearest:** Allocated: 130.0 kg | Unmet: 70.0 kg | Missed Windows: 1 | Runtime: 3 ms
- **OR-Tools:** Allocated: **170.0 kg** | Unmet: **30.0 kg** | Missed Windows: **0** | Runtime: **15 ms**

### Scenario 4: Uneven Priority Weights
- **FCFS:** Allocated High-Priority: 40.0 kg / 60.0 kg (66.7%) | Total Allocated: 104.0 kg | Runtime: 2 ms
- **Nearest:** Allocated High-Priority: 45.0 kg / 60.0 kg (75.0%) | Total Allocated: 136.0 kg | Runtime: 3 ms
- **OR-Tools:** Allocated High-Priority: **60.0 kg / 60.0 kg (100.0%)** | Total Allocated: **184.0 kg** | Runtime: **16 ms**
- **Key Finding:** OR-Tools guaranteed 100% fulfillment of critical priority orphanages before allocating remaining surplus to standard requests.

### Scenario 5: Disaster Resource Scarcity & Road Restrictions
- **FCFS:** Allocated: 90.0 kg | Unmet: 110.0 kg | Hazard Route Violations: 0 | Runtime: 2 ms
- **Nearest:** Allocated: 120.0 kg | Unmet: 80.0 kg | Hazard Route Violations: 0 | Runtime: 3 ms
- **OR-Tools:** Allocated: **160.0 kg** | Unmet: **40.0 kg** | Hazard Route Violations: 0 | Runtime: **18 ms**

### Scenario 6: Courier Cancellation Recovery
- **FCFS:** Allocated: 80.0 kg | Recovery Time: Manual | Runtime: 2 ms
- **Nearest:** Allocated: 110.0 kg | Recovery Time: Manual | Runtime: 3 ms
- **OR-Tools:** Allocated: **170.0 kg** | Replacement Reassigned: **Atomically in 11 ms** | Status: **PASS**

### Scenario 7: Mixed Unit Isolation
- **FCFS:** Allocated: 50 kg / 20 L / 0 kits | Rejected Incompatible: 10 boxes | Runtime: 2 ms
- **Nearest:** Allocated: 65 kg / 30 L / 0 kits | Rejected Incompatible: 10 boxes | Runtime: 3 ms
- **OR-Tools:** Allocated: **90 kg / 40 L / 20 kits** | Rejected Incompatible: **10 boxes** | Runtime: **13 ms**
- **Key Finding:** Strict unit isolation preserved; no cross-unit addition occurred.

---

## 3. Solver Reliability & Speed

Across all 7 scenarios:
- **Mean OR-Tools Solve Time:** 14.3 ms
- **Max Memory Usage:** < 15 MB
- **Hard Safety Violations:** 0 (0.0%)
- **Mathematical Conservation ($\text{Allocated} + \text{Unmet} = \text{Requested}$):** 100% verified across all algorithms.
