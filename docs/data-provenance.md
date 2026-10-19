# NeighborNet AI — Data Provenance & Limitations Documentation

## 1. Data Classification

| Dataset Class | Current Repository Context | Usage in Phase 4 | Limitations |
|---|---|---|---|
| **Development Seed Data** | Generated via `seed_demo.py` for Moratuwa/Colombo South pilot region. | Functional testing, API verification, coordinator dashboard demonstration. | Fictional names, organizations, and telephone numbers. Cannot be claimed as real partner operational records. |
| **Synthetic Evaluation Fixtures** | Programmatically created in `management/commands/evaluate_intelligence.py` and test suites. | Standardized algorithmic comparison (OR-Tools vs FCFS vs Nearest). | Deterministic synthetic numbers with known ground truth to stress test edge cases. |
| **Geospatial Reference Points** | Authentic coordinates in Moratuwa, Ratmalana, Dehiwala, Colombo South (EPSG:4326). | PostGIS bounding queries, service area radius (<35 km), Haversine straight-line distance. | Straight-line distance approximations. Does not reflect live real-time traffic or flood barriers without dedicated sensor integration. |

---

## 2. Privacy & Volunteer Protection

- **Volunteer Locations:** Exact real-time GPS coordinates of volunteer couriers are stored only for dispatch proximity calculations and are never exposed via unauthenticated or public API responses.
- **Organization Addresses:** Recipient shelter addresses and donor facility addresses are restricted to authenticated participating roles and system coordinators.

---

## 3. Forecasting Justification & Deferred Status

Under Section 16 & 17 of the Phase 4 specification:
1. **Real-world time-series data requirement:** Training a machine learning model (e.g. Scikit-learn or LightGBM) on synthetic seed records and asserting real-world predictive accuracy would violate competition integrity guidelines.
2. **Current state:** Operational records in the pilot database represent point-in-time scenarios rather than a multi-year historical log.
3. **Action:** Machine learning demand/surplus forecasting is marked as **DEFERRED**.
4. **Active Capabilities:** Comprehensive descriptive intelligence analytics powered by Pandas and NumPy calculate real-time ratios, fulfillment percentages, category distributions, and shelf-life vulnerability directly from PostgreSQL records.
