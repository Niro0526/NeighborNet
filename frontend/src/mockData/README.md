# NeighborNet AI — Centralized Mock Data Architecture

This directory houses the single source of truth for all mock and prototype data in NeighborNet AI.

## Architectural Principles
1. **Never mutate imported seed arrays**: Use the in-memory mock repository (`src/services/mockRepository.ts`) which clones seeds and provides transactional mutations.
2. **Never hardcode values inside components**: Pages and components only consume asynchronous typed services from `src/services/`.
3. **Consistent Entity IDs**: All foreign keys across users, organizations, food listings, requests, delivery tasks, and AI insights link directly to valid entities.
4. **Geographic Fidelity**: Realistic geographic points within the Moratuwa / Mount Lavinia / Dehiwala / Colombo corridor, Sri Lanka.
5. **No Fake Claims**: Clearly tagged as **Demo Recommendation — Simulated** or **Simulated Operational Data**.

## Dataset Mapping
- `users.ts`: Demo user accounts for each of the 4 platform roles (`FOOD_PROVIDER`, `RECIPIENT`, `VOLUNTEER`, `COORDINATOR`).
- `organizations.ts`: Food donors, NGOs, shelters, and disaster response centers.
- `foodListings.ts`: Surplus food items with quantities, dietary badges, safety deadlines, and storage temperatures.
- `resourceRequests.ts`: NGO community needs and disaster emergency supply requests.
- `volunteers.ts`: Volunteer couriers with vehicle types, capacities, ratings, and live status.
- `deliveryTasks.ts`: Full task state machine (`AVAILABLE` -> `ACCEPTED` -> `ARRIVED_PICKUP` -> `PICKED_UP` -> `ARRIVED_DELIVERY` -> `DELIVERED`).
- `disasterEvents.ts`: Declared emergencies, affected zones, impacted population, and relief deficit tracker.
- `allocations.ts`: Matching algorithm results with compatibility scores and rationales.
- `aiInsights.ts`: Simulated AI recommendations (Food Match, Expiry Risk, Bottleneck, Route Disruption).
- `notifications.ts`: Role-targeted system and alert messages.
- `activityLogs.ts`: System audit trail and event ledger.
- `mapLocations.ts`: Coordinated geospatial markers and bounds.
- `analytics.ts`: Trend aggregations derived strictly from mock records.
- `scenarios.ts`: One-click interactive scenarios for ModelX demonstration.
