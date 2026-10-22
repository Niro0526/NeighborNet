# NeighborNet AI role integration audit — 22 October 2026

**Overall result: PARTIAL PASS.** The React → DRF → PostgreSQL delivery workflows passed real browser testing, including disaster disruption and courier replacement. **Requested PostGIS execution is FAIL / BLOCKED:** this PostgreSQL installation does not offer the PostGIS extension, and the application is configured with `USE_POSTGIS=False`. This report does not certify PostGIS, all secondary product pages, or production readiness.

The existing dashboard components were retained. Changes connect their data, actions, permissions and routes; no deployment, push or commit was performed. Pre-existing working-tree changes were preserved.

## Runtime and method

- React/Vite: `http://127.0.0.1:5173`; `.env` uses `VITE_DATA_SOURCE=api`, with `/api/v1` proxied to Django.
- Active Django project: `backend/`, served on `127.0.0.1:8000` with development settings.
- Database: `neighbornet_db`, PostgreSQL 18.3. Queried server version, database name and installed extensions directly. Installed extensions contain only `plpgsql`; querying available extensions for `postgis` returns no rows. No SQLite substitution was used.
- Real in-app browser sessions signed in and out as each actor. These were sequential authenticated sessions, not simultaneous isolated browser profiles. Independent HTTP sessions supplemented negative permission checks.
- PostgreSQL snapshots were captured between actions. They include resources, requests, allocations, tasks, timestamped status events, notifications and final role/audit records. They contain local demo account information; keep this evidence local.
- Screenshots and DOM captures are in [integration-evidence](integration-evidence/). [Final database snapshot](integration-evidence/33-final-database.json), [database assertions](integration-evidence/database-assertions.json), and [live HTTP evidence](integration-evidence/live-api-permissions.json) support the results below.

## Records traced

| Workflow | Resource | NGO request | Allocation | Delivery | Quantity / outcome |
|---|---|---|---|---|---|
| Community food | `RES-0F5A7E` | `REQ-A5664C` | `ALC-2DCAE7` | `TSK-658A5B` | 15 kg, delivered by Dinesh and received by NGO |
| Disaster relief | `RES-9189C7` | `REQ-966CB0` | See final snapshot | `TSK-D03D31` | 5 kg, disrupted, reassigned from Dinesh to Kasun, then received by NGO |

Both resources end `COLLECTED`; both allocations and NGO requests end `FULFILLED`; both tasks end `DELIVERED`. Reserved inventory equals the lot quantity, with zero available. The failed first deadline request `REQ-8EAFC7` was retained as `CANCELLED` and replaced by the valid v2 request.

## Step-by-step PASS / FAIL results

| Step | Result | Browser action and observed outcome | PostgreSQL / other evidence |
|---|---|---|---|
| 1. Run actual frontend and backend in API mode | PASS | Authenticated dashboards loaded through Vite and Django session authentication. | PostgreSQL engine/version in [final snapshot](integration-evidence/33-final-database.json); API services use real HTTP. |
| 2. Run PostgreSQL/PostGIS | **FAIL / BLOCKED** | PostgreSQL works; PostGIS is unavailable locally. Docker daemon is also not running. | `extensions: [plpgsql]`; plain PostgreSQL backend. Spatial SQL and PostGIS operators were not tested. |
| 3. Food Provider sign-in and listing | PASS | Fathima published `AUDIT-20261022 Bread Delivery`, 15 kg, with a custom pickup address. Listing appeared in provider inventory. | [Provider screenshot](integration-evidence/01-provider-lot.png); [before-allocation snapshot](integration-evidence/03-before-allocation-database.json). |
| 4. NGO sees provider inventory | PASS | Sister Mary saw the new lot in the recipient catalog/dashboard. | [NGO screenshot](integration-evidence/02-recipient-request.png); same resource ID persisted. |
| 5. NGO submits request with a usable deadline | **Initial FAIL → fixed PASS** | Initial local-time default produced a past deadline and prevented matching. Fixed default timezone conversion and server validation; v2 request appeared in the NGO dashboard. | `REQ-A5664C`, 15 kg. Failed request retained and later cancelled. [Coordinator eligible pair](integration-evidence/03-coordinator-match.png). |
| 6. Coordinator screens and optimizes | PASS | Kaveen saw the exact provider/NGO pair, ran OR-Tools, and reviewed 15 kg assigned to Dinesh. | Batch `OPT-EBB45B`; [matching screenshot](integration-evidence/03-coordinator-match.png). |
| 7. Coordinator approves and commits | PASS | Approved the plan, then used Apply & Commit. Inventory reserved, request allocated, and courier task created. | [Allocation snapshot](integration-evidence/04-allocated-database.json); task `TSK-658A5B` starts `ACCEPTED` because the plan assigns a courier. |
| 8. Volunteer sees assignment and correct pickup | PASS | Dinesh's session showed the audit delivery and `Audit Pickup Desk, Moratuwa`, rather than the provider's default address. | [Volunteer assignment](integration-evidence/05-volunteer-assigned.png); persisted `pickup_address`. |
| 9. Volunteer arrives at pickup | PASS | Clicked Mark Arrived at Pickup; next action became Confirm Food Picked Up. | [Browser](integration-evidence/06-arrived-pickup.png), [database](integration-evidence/06-arrived-pickup-database.json). |
| 10. Volunteer collects goods | PASS | Clicked Confirm Food Picked Up; task became `PICKED_UP`. | [Browser](integration-evidence/07-picked-up.png), [database](integration-evidence/07-picked-up-database.json). |
| 11. Volunteer reaches NGO | PASS | Clicked Mark Arrived at Drop-off; task became `ARRIVED_DELIVERY`. | [Browser](integration-evidence/08-arrived-delivery.png), [database](integration-evidence/08-arrived-delivery-database.json). |
| 12. NGO confirms final receipt | PASS | Sister Mary's independent login showed the arrival and Confirm Receipt action. Receipt changed task/allocation/request to their completed states. | [NGO fulfilled](integration-evidence/09-recipient-fulfilled.png), [delivered snapshot](integration-evidence/09-delivered-database.json). Last event actor is the NGO. |
| 13. Notifications persist and appear | PASS | NGO inbox displayed allocation, collection, arrival and completion messages. Unread badge now uses the API's actual field. Mark-all-read persisted. Provider and couriers also received direct audit notifications. | [Inbox screenshot](integration-evidence/11-recipient-notifications.png); notification rows in final snapshot; 12/12 final DB assertions pass. |
| 14. Role and organization boundaries | PASS | NGO opening admin dashboard received Coordinator Authorization Required. Independent HTTP checks rejected cross-provider inventory mutation, volunteer food creation, direct task PATCH, role escalation, missing CSRF, other-courier completion and repeated receipt. | [Browser denial](integration-evidence/10-recipient-admin-denied.png); [19/19 HTTP checks](integration-evidence/live-api-permissions.json). |
| 15. Provider + Volunteer account | PASS | Ravi saw both modules, opened food listings and volunteer tasks without changing identity. | [Combined dashboard](integration-evidence/12-multirole-provider-volunteer.png), [task view](integration-evidence/13-multirole-tasks.png). |
| 16. Recipient + Volunteer account | PASS | Anuki saw her own NGO request and courier operations together. Recipient shipments were scoped separately from courier assignments. | [Combined dashboard](integration-evidence/28-multirole-recipient-volunteer.png). |
| 17. Coordinator + Volunteer account | PASS | Malik saw courier operations and Administration Workspace in the same account, then exercised Coordinator mode resolution. | [Combined dashboard](integration-evidence/29-multirole-coordinator-volunteer.png), [mode resolution](integration-evidence/30-coordinator-normal-restored.png). |
| 18. Coordinator activates disaster mode | **Initial FAIL → fixed PASS** | Fixed the UI-only mode toggle and disaster-create field mismatch. Activation persisted as `DIS-392CA0`, and Coordinator dashboard showed emergency mode. | [Browser](integration-evidence/14-coordinator-disaster-active.png), [database](integration-evidence/14-disaster-active-database.json). |
| 19. Provider and NGO receive disaster context | PASS | Provider displayed emergency mode and published 5 kg relief supply; NGO displayed the same event and submitted an urgent linked request. | [Provider](integration-evidence/15-provider-disaster.png), [relief lot](integration-evidence/16-provider-relief-lot.png), [NGO](integration-evidence/17-recipient-disaster.png), [request](integration-evidence/18-recipient-relief-request.png). Both records reference `DIS-392CA0`. |
| 20. Coordinator dispatches disaster allocation | PASS | Ran optimizer in Disaster Response context, approved and applied 5 kg allocation to Dinesh. | Batch `OPT-60B2F0`; [dispatch browser](integration-evidence/19-disaster-dispatch.png), [database](integration-evidence/19-relief-dispatched-database.json). |
| 21. Volunteer reports road disruption | PASS | Dinesh submitted the named audit road closure. His mission became `DISRUPTED`, with the reason visible. Coordinator alert and disruption state persisted. | [Volunteer](integration-evidence/21-volunteer-disrupted.png), [database](integration-evidence/21-disrupted-database.json), [Coordinator](integration-evidence/22-coordinator-disruption-alert.png). |
| 22. Coordinator previews and applies recovery | **Broken connection fixed → PASS** | Recovery showed the correct original courier/status/quantity, proposed Kasun, and applied replacement. The same task resumed `ACCEPTED`, rather than becoming an unusable assigned-but-available mission. | [Preview](integration-evidence/23-coordinator-recovery-preview.png), [applied](integration-evidence/24-coordinator-recovery-applied.png), [database](integration-evidence/24-reassigned-database.json). |
| 23. Replacement courier completes transport | PASS | Kasun signed in with his existing demo account, saw the same mission, marked pickup arrival, collection and NGO arrival. | [Replacement session](integration-evidence/25-replacement-volunteer.png), [arrival](integration-evidence/26-replacement-arrived.png). |
| 24. NGO receives recovered delivery | PASS | Sister Mary confirmed receipt of the 5 kg disaster lot; both audit requests show fulfilled. | [NGO](integration-evidence/27-disaster-fulfilled.png), [database](integration-evidence/27-disaster-delivered-database.json). |
| 25. Coordinator resolves mode across roles | PASS | Malik's Coordinator role resolved the audit emergency. Final database contains no ACTIVE disaster. Provider session and completed allocations remain accessible after reload. | [Normal mode](integration-evidence/30-coordinator-normal-restored.png); [final assertions](integration-evidence/database-assertions.json). |
| 26. Final authorized dashboard reconciliation | PASS | Provider allocations show both completed lots; Coordinator inventory shows both collected lots; Coordinator requests show both fulfilled demands; courier completion counts and NGO confirmations persist. | [Provider](integration-evidence/34-provider-final-allocations.png), [Coordinator inventory](integration-evidence/31-coordinator-inventory.png), [Coordinator requests](integration-evidence/32-coordinator-requests.png), [final snapshot](integration-evidence/33-final-database.json). |
| 27. Pending approval, self-claim, provider handover, partial delivery and per-user read isolation | PASS — automated coverage | Regression tests exercise these alternative paths. The browser workflows above use optimizer-assigned couriers; a separate browser self-claim scenario was not run. | [Regression tests](../backend/tests/test_role_integration_regressions.py); final targeted 6 tests passed. |

## Persisted event sequences

`TSK-658A5B`: `INITIAL → ACCEPTED → ARRIVED_PICKUP → PICKED_UP → ARRIVED_DELIVERY → DELIVERED`.

`TSK-D03D31`: `INITIAL → ACCEPTED → DISRUPTED → ACCEPTED → ARRIVED_PICKUP → PICKED_UP → ARRIVED_DELIVERY → DELIVERED`. Reassignment preserves the task, resource, request and allocation IDs. The original courier receives no completion increment for this reassigned delivery; Kasun receives the completion.

Both final receipt events are attributed to `sister.mary@graceeldercare.org`. [Machine-readable assertions](integration-evidence/database-assertions.json) verify the sequences, quantities, final states and notification recipients.

## Fixes made

- Enforced approved roles, active organization membership, organization type/verification, and object ownership for mutations; blocked generic task state editing/creation and raw allocation mutation.
- Added request-demand, finite quantity, unit/category, expiry and operating-event checks; protected reserved inventory against invalid editing/withdrawal/cancellation.
- Locked delivery transitions and courier claims transactionally; gated claims on approved allocations and courier readiness; prevented unauthorized transitions, duplicate completion and false full fulfillment of partial deliveries.
- Preserved remaining lot availability after partial pickup and prevented marking an entire multi-allocation lot collected before all pickups.
- Connected optimizer application to status history and notifications; required explicit plan approval; revalidated stale inventory/demand and active relief events.
- Repaired recovery assignment state, preserved earlier delivery phase, added status events, revalidated replacement availability, and stopped marking infeasible recovery as successful. New recovery business notifications also target provider/recipient organizations.
- Fixed unread-count contract, removed sliced notification detail queryset, restricted generic notification mutation, and created independent per-user broadcast inbox entries for new notifications.
- Added paginated collection loading, membership-aware module filtering, dashboard polling, accurate zero values, expiry visibility, correct allocation units and delivered-kg totals.
- Connected existing recipient tracking/catalog/request, volunteer task, Coordinator inventory/request/disaster, and completion-notification destinations to existing functional views. Retained existing component layouts.
- Repaired disaster API payloads and persisted mode transitions, refreshed state on account changes and polling, and preserved mode during non-authentication network errors.
- Corrected provider/recipient time defaults. Exposed mode activation errors instead of silently closing the confirmation.
- Corrected stale selected recommendation data after applying a plan and recovery preview response-field mapping.
- Configured the existing pickup-map worker as a Vite-served asset. This builds successfully; PostGIS and full map-tile/spatial behavior remain outside the verified PASS scope.
- Made the old E2E helper's live-server targeting opt-in with `NEIGHBORNET_LIVE_TESTS=1`; ordinary pytest runs now use the separate test database. Updated expired hardcoded test dates and fixtures to reflect verified membership/courier requirements.

## Validation and limits

| Check | Result |
|---|---|
| Full backend suite | **47 passed**, PostgreSQL test database, 300.69 seconds |
| Final targeted delivery/permissions/recovery regression run | **6 passed**, 29.48 seconds |
| Final database assertions | **12 / 12 PASS** |
| Live HTTP permission/dashboard checks | **19 / 19 PASS** |
| React TypeScript + Vite build | **PASS**, with existing large-bundle warning |
| Django system check / Git whitespace check | **PASS** |
| PostGIS extension / spatial execution | **FAIL / BLOCKED**, extension unavailable |
| Simultaneous browser profiles and concurrency stress | **NOT RUN**; row locking is implemented and covered by backend tests, not a browser load test |
| Full secondary-page audit (partner directory, fleet administration, courier history, audit page, settings) | **NOT CERTIFIED**; some remain existing placeholders, and no new feature implementations were added |

The database contained three ACTIVE seeded disasters, old deliveries, expired lots and accumulated demo records. Mode tests resolved those events, created the audit emergency and resolved it. The first legacy pytest run auto-detected the live server before that helper was fixed, adding local test records such as `RES-7E81A8` and `REQ-1E6F99`; later runs were isolated. Existing delivery history was not purged. Final audit records are identified above so they can be distinguished from that data.

New per-user notification behavior is verified for newly emitted business events; historical shared broadcast rows were not migrated. Browser screenshots reflect the action-time versions, with later corrections additionally verified through final dashboards, API checks and targeted regressions.

Local frontend/backend servers remain running for review. The provider browser tab is retained. No code was pushed or deployed.

## Reproduce final evidence

From `backend/`:

```powershell
python audit_assertions.py
python audit_integration.py review
python audit_live_permissions.py
python -u -m pytest tests -q -p no:cacheprovider --reuse-db --tb=short
```

`audit_integration.py` and `audit_assertions.py` are read-only against operational data. `audit_live_permissions.py` signs into existing local demo accounts, performs negative checks and idempotently cancels only the named failed audit request. Its outputs go to `docs/integration-evidence/`.
