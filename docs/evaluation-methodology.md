# NeighborNet AI — Evaluation Methodology & Competition Benchmarks

## 1. Benchmarking Protocol

To provide reproducible evaluation for the ModelX 2.0 competition, NeighborNet AI implements a standardized test harness invoked via:

```bash
python manage.py evaluate_intelligence
```

The benchmark runs all three allocation engines against **identical input snapshots**, **identical hard safety constraints**, and a **frozen reference timestamp** (`2026-10-15 12:00:00 UTC`):
- **Baseline A:** First-Come-First-Served (FCFS) Chronological Allocation.
- **Baseline B:** Nearest Compatible Match (Greedy Proximity).
- **Advanced Optimizer:** Google OR-Tools CP-SAT ($S=100$ scale factor).

---

## 2. Standardized Evaluation Metrics

1. **Total Requested Quantity (kg):** Total mass of requested demand.
2. **Total Eligible Requested Quantity (kg):** Demand passing hard constraints.
3. **Total Allocated Quantity (kg):** Total mass allocated by algorithm.
4. **Total Unmet Quantity (kg):** Residual unfulfilled demand.
5. **Quantity Fulfillment Percentage (%):** $(\text{Allocated Qty} / \text{Total Requested Qty}) \times 100$.
6. **Request Fulfillment Percentage (%):** $(\text{Fully Satisfied Requests} / \text{Total Requests}) \times 100$.
7. **Priority-Weighted Demand Fulfillment (%):** Priority-scaled demand fulfillment ratio.
8. **Fully Satisfied Requests Count:** Number of requests receiving 100% of requested demand.
9. **Partially Satisfied Requests Count:** Number of requests receiving $>0\%$ but $<100\%$ of demand.
10. **Unserved Requests Count:** Number of requests receiving $0\%$ allocation.

---

## 3. Verified Benchmark Results (Frozen Reference Dataset)

Dataset Identifier: `MODELX_EVAL_BENCHMARK_V1` | Reference Timestamp: `2026-10-15 12:00:00 UTC`

### Scenario A: Normal Community Mode (Balanced 200.0 kg Demand)
```
====================================================================================================================================================
Comprehensive Metric Verification (Normal Community Mode (Balanced)):
====================================================================================================================================================
Algorithm              | Alloc (kg) | Unmet (kg) | Qty Ful %  | Req Ful %  | Wtd Ful %  | Fully/Part/Unserved  | Conservation Check
----------------------------------------------------------------------------------------------------------------------------------------------------
Baseline A (FCFS)      | 180.0      | 20.0       | 90.0%      | 66.7%      | 93.2%      | 2 / 1 / 0            | PASS (180.0 + 20.0 = 200.0 kg)
Baseline B (Nearest)   | 180.0      | 20.0       | 90.0%      | 66.7%      | 93.2%      | 2 / 1 / 0            | PASS (180.0 + 20.0 = 200.0 kg)
OR-Tools CP-SAT        | 180.0      | 20.0       | 90.0%      | 66.7%      | 93.2%      | 2 / 1 / 0            | PASS (180.0 + 20.0 = 200.0 kg)
====================================================================================================================================================
```

### Scenario B: Disaster Response Mode (Resource Scarcity 140.0 kg Supply vs 200.0 kg Demand)
```
====================================================================================================================================================
Comprehensive Metric Verification (Disaster Response Mode (Resource Scarcity)):
====================================================================================================================================================
Algorithm              | Alloc (kg) | Unmet (kg) | Qty Ful %  | Req Ful %  | Wtd Ful %  | Fully/Part/Unserved  | Conservation Check
----------------------------------------------------------------------------------------------------------------------------------------------------
Baseline A (FCFS)      | 140.0      | 60.0       | 70.0%      | 33.3%      | 72.9%      | 1 / 2 / 0            | PASS (140.0 + 60.0 = 200.0 kg)
Baseline B (Nearest)   | 140.0      | 60.0       | 70.0%      | 33.3%      | 72.9%      | 1 / 2 / 0            | PASS (140.0 + 60.0 = 200.0 kg)
OR-Tools CP-SAT        | 140.0      | 60.0       | 70.0%      | 33.3%      | 72.9%      | 1 / 2 / 0            | PASS (140.0 + 60.0 = 200.0 kg)
====================================================================================================================================================
```
