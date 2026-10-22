# Personal community food requests

Open `/community-food` from any authenticated account. Individual registration creates a real Django user without an NGO, organization membership, or privileged role. Organization roles remain optional and retain their existing verification and membership checks.

Save an address and coordinates, read the food storage/safety instructions, select quantity and delivery or pickup, and click Request food. Inventory is reserved atomically while awaiting coordinator approval. The provider, recipient, and approved coordinators receive persisted inbox notifications at each transition. The page polls the API every 15 seconds.

Delivery: PENDING → APPROVED → ASSIGNED → PICKED_UP → DELIVERED → RECEIVED.

Pickup: PENDING → APPROVED → PICKED_UP → RECEIVED. Approval generates a private pickup code visible only to the recipient. The provider or coordinator verifies that code and safe handling before recording handover. Only the recipient can confirm receipt.

Pending requests may be rejected by coordinators. Recipients or coordinators may cancel before pickup; inventory is released exactly once, and an assigned volunteer becomes available again. A unique database constraint and inventory row lock prevent duplicate requests and oversubscription, including competition with existing NGO allocations. Completed claims cannot be repeated for the same food lot.

Eligibility requires an active account, verified provider, normal-mode food, documented storage requirements, a safe-consumption deadline at least two hours away for requests/approval, an open future pickup window, stock, and a location inside the existing service radius. Pickup rechecks safety and the actual pickup start time. Disaster supplies remain exclusively in the existing emergency workflow. Verified, available volunteers can accept deliveries within their capacity in kg; offers measured in other units use authorized pickup because the system has no reliable weight conversion.

API (session authentication and CSRF on mutations):

| Endpoint | Purpose |
| --- | --- |
| GET/PUT `/api/v1/community-food/location/` | Own saved location |
| GET `/api/v1/community-food/offers/` | Eligible normal food, sorted by distance when location is saved |
| GET/POST `/api/v1/community-food/` | Scoped tracking and new request |
| GET `/api/v1/community-food/{id}/` | Authorized claim detail |
| POST `/api/v1/community-food/{id}/transition/` | Authorized state transition |

Request body: `resource`, `quantity` (positive, at most two decimal places; defaults to 1), `method` (`delivery` or `pickup`), `safetyAcknowledged: true`.

Transition body: `status`; pickup also requires `safetyAcknowledged: true` and, for recipient pickup, `pickupCode`. State, actor, and timestamp are recorded as server-generated events. Arbitrary PATCH/DELETE operations are unavailable. Providers and unassigned volunteer pool viewers cannot read private recipient addresses or pickup codes.

Coordinates and immutable request location snapshots are persisted in PostgreSQL. When the connected database has PostGIS enabled, eligibility uses `ST_DistanceSphere`; otherwise it uses the existing Haversine calculation. This workstation's PostgreSQL installation does not include PostGIS, so spatial-extension execution cannot be verified here.

Verification: run `python -m pytest tests/test_personal_food_claims.py tests/test_donation_tracking.py tests/test_role_integration_regressions.py tests/test_disasters.py -q` from `backend`. Tests use real Django APIs and a separate PostgreSQL test database, including concurrent transactions, actual registration/session/CSRF handling, both fulfillment paths, notifications, privacy, and existing NGO/disaster regressions. No mock repository or mock API responses are used. Frontend validation: `npm run build` from `frontend`.
