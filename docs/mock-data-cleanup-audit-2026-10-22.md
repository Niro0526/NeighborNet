# NeighborNet AI — mock/demo cleanup audit, 22 October 2026

Confirmed disposable data was removed after a full PostgreSQL backup. **593 rows were deleted**, including 25 listings, 41 requests, their confirmed dependent transactions, and 10 unused benchmark organizations. All 11 users and all role assignments, memberships, and volunteer profiles were preserved. The remaining 8 organizations were preserved. No database reset, Git push, deployment, dashboard redesign, or application-schema migration was performed for this cleanup.

The requested new-listing/new-request browser checks passed. **The database is not certified free of all historical synthetic data:** ambiguous older workflows and their connected records were deliberately retained. PostgreSQL persistence proves storage and integration, not real-world authenticity.

## Backup and deletion safeguards

- Database: `neighbornet_db`, PostgreSQL 18.3. The running backend uses `backend/`; the frontend is Vite in API mode at `http://127.0.0.1:5173`, with Django at `http://127.0.0.1:8000`.
- Canonical backup: [before-cleanup.dump](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/backups/cleanup-20261022-071517/before-cleanup.dump), created before any cleanup deletion.
- Archive size: **185,811 bytes**. SHA-256: `96802b10aefe5fda40e261f56b5ff563ce2ff0c344ec359d6e2f28a03eee91a9`.
- `pg_restore --list` succeeded, and decoding the complete archive to SQL with output discarded succeeded. A full restore into a second database was **not** performed; the application database was never overwritten.
- Backup, catalog, inventory, and manifest are under `backups/cleanup-20261022-071517/`. `backups/` is Git-ignored because the archive includes private application data.
- Cleanup selected frozen inventory IDs, checked that selected resource/request dependencies did not cross into unconfirmed workflows, previewed Django's cascade collector, and deleted in transactions. Target resource/request rows had to match their backed-up values before deletion.
- Identity/profile fingerprints matched before and after the first cleanup. The subsequent benchmark-organization cleanup separately verified that the 10 exact fixture organizations had no dependent rows and that every other organization remained unchanged. Browser/API logins afterward legitimately update authentication metadata.
- Recently created listing **`RES-BC62CE` (“Eggs”)** was preserved; its entire row still equals the pre-cleanup inventory.

## What was deleted

| PostgreSQL model | Deleted rows |
|---|---:|
| Resource / Food Listing | 25 |
| Resource Request | 41 |
| Allocation | 24 |
| Delivery Task | 24 |
| Delivery Status Event | 48 |
| Notification | 217 |
| Activity Log | 141 |
| Pilot Feedback | 3 |
| Evaluation Metric Run | 48 |
| Recommendation Batch | 3 |
| Optimization Recommendation | 5 |
| Disruption Event | 1 |
| Disaster Event | 3 |
| Unreferenced benchmark Organization | 10 |
| **Total** | **593** |

Listing provenance: 3 exact `seed_demo` primary keys (`RES-001`, `RES-002`, `RES-003`); 1 exact `[DEMO]` pilot listing; 2 documented `AUDIT-20261022` browser-audit listings; and 19 repeated live-test listings matching the name, provider, category, quantity, unit, and dietary-tag signature in `test_e2e_scenarios.test_scenario_a_food_rescue`.

Request provenance: 1 exact seed request (`REQ-001`); 1 exact `[DEMO]` pilot request; 3 documented audit requests; 19 exact scenario-A payload signatures; and 17 exact scenario-C emergency-water payload signatures. Dependent allocations, delivery events, notifications with matching event keys, and recommendations were inspected through their foreign keys.

Activity cleanup removed 36 explicitly linked seed/audit/ID records, then 105 additional entries correlated with the deleted workflows by exact resource/request names, expected actions, and timestamps within two seconds of creation or delivery transitions. Creation entries also required the original creator. Generic login/logout history was preserved.

The removed disasters were `EVT-ADV-DISASTER`, `EVT-DISASTER-01`, and the documented audit event `DIS-392CA0`. `DIS-001` was retained because it remains connected to unconfirmed records.

The 10 removed organizations were the exact `EVAL-ORG-P1/P2/P3/R1/R2/R3` and `ADV-ORG-P1/P2/R1/R2` fixtures. Their names and IDs matched the fixture source, and they had no dependent rows. They are now available in the separate benchmark database.

Exact IDs and provenance are recorded in:

- [Transactional cleanup ledger](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/cleanup-result.json), including cascade-deleted IDs.
- [Benchmark organization ledger](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/benchmark-organization-cleanup.json).
- [Additional activity ledger](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/activity-cleanup.json), including each removed entry and timestamp.

## What was intentionally retained

| Retained record | Reason |
|---|---|
| `RES-BC62CE` — Eggs | Recent pre-existing listing; no disposable-demo provenance. Entire row verified unchanged. |
| `RES-46085B`, `RES-6BAA3D`, `RES-ECE370`, `RES-D5D082` — Rice & Curry Packets | Suspicious older records, but no sufficiently reliable source provenance found. |
| `REQ-116FA8`, `REQ-AE23BB`, `REQ-493FD9`, `REQ-54EAFF` — Cooked Meals Requisition | Same uncertainty; connected allocations and tasks preserved. |
| `REQ-CF32DD` — Emergency Potable Water 500L | Unconfirmed origin; preserved. |
| `RES-004`, `REQ-002`, `DIS-001` | Known seed records connected to unconfirmed workflows; preserved to avoid damaging those workflows. |
| `OPT-2DBD01` and its remaining recommendations | Mixed dependencies involving retained data; batch preserved. Confirmed deleted-resource recommendations were removed through their cascade. Historical batch aggregate metadata was not rewritten. |
| All 11 users; remaining 8 organizations | Existing accounts, organizations, memberships, and profile metadata protected, including known seed/demo identities. These are not certified genuine human/organization records. |
| Generic authentication/activity history and unmatched notifications | No record-specific evidence justified deleting them. |

Historical raw volunteer profile counters and ratings were retained with the profiles. API completion counts now derive from persisted delivered tasks rather than seeded completion-counter values. Other retained metadata is not a claim of real-world authenticity.

The final application database contains **7 listings, 7 requests, 7 allocations, 8 delivery tasks, 17 notifications, 11 users, and 8 organizations**. Those listing/request totals include the two new, explicitly named verification records below. No benchmark evaluation runs remain in the application database.

## Code and environment fixes

- API mode no longer initializes the mock repository from seed arrays or old demo local-storage state. The API user-switch shortcut is disabled, API login fields start blank, and the demo account helper is hidden in API mode. Explicit offline mock mode remains available for development; its records are not merged into API results.
- Removed the API map-location failure fallback to mock organizations, invented map coordinates/postcodes, fixed mock analytics-series returns in API mode, and loaded all organization pages. Unsupported old chart-series methods return no fabricated dataset; existing verified impact analytics still query Django.
- Removed fabricated adapter IDs, creation/deadline timestamps, organization IDs, disaster population/team/request counts and supply summaries, distance/duration samples, volunteer capacity/rating/badge defaults, and sampled route/GPS claims. Neutral placeholders or unavailable/empty values replace invented data. Actual serializer fields supply records and metrics.
- Disaster request/team counts are calculated from PostgreSQL. Volunteer completion counts use persisted delivered tasks. Coordinator activity now reads the serializer's actual timestamp and user-name fields. Removed the invented public “1,240+ kg” total and a fixed optimization-score/zero-violations claim.
- Listing/request APIs default to `-created_at, -id`; frontend services also sort returned records newest-first. Existing Provider, NGO, and Coordinator cards now display primary keys and creation timestamps. Request creation shows the returned request ID and no longer supplies the sample NGO identity in API mode.
- Added `config.settings.benchmark`, targeting **`neighbornet_db_benchmark`**, created that separate database, migrated its empty schema, and ran both benchmark suites there. It contains **10 fixture organizations and 30 evaluation runs**; the application database contains zero benchmark runs.
- Seed commands and fixture organization loaders refuse the application database, including `--force` / `--force-demo`. Equivalent legacy root seed/fixture entry points and the alias-user script are guarded. Both E2E test entry points require explicit `NEIGHBORNET_LIVE_TESTS=1` before using a running server; default tests use the separate Django test database.

Run synthetic datasets explicitly against the separate environment, for example `python manage.py evaluate_intelligence --settings=config.settings.benchmark` from `backend/`. No application data is reset by this workflow.

## Step-by-step verification

| Step | Result | Evidence |
|---|---|---|
| 1. Full backup before deletion, archive catalog/read validation | PASS | Backup manifest, archive catalog, full SQL decoding exit code 0. Restore rehearsal not performed. |
| 2. Delete only confirmed records and protect identities/dependencies | PASS | Transaction ledgers and matching protected fingerprints; Eggs row unchanged. |
| 3. Prevent seed/benchmark writes in application DB | PASS | Actual `seed_demo --force` refused; 9 isolation tests passed. |
| 4. Run fixtures in a separate environment | PASS | Standard and advanced commands succeeded in `neighbornet_db_benchmark`; 30 runs there, zero in application DB. |
| 5. Provider signs in and submits a new 2 kg bakery listing through React | PASS | `RES-5980F3`, creator `USR-002`, provider `ORG-002`; PostgreSQL row and Provider screenshot. |
| 6. Provider refreshes My Food | PASS | New listing remains first, above preserved Eggs, with stable ID/time. |
| 7. Separate NGO sign-in sees Provider listing, including after refresh | PASS | NGO dashboard card, actual provider name, 2 kg, `RES-5980F3`; browser screenshot and DOM evidence. |
| 8. NGO submits a new 2 kg request through React | PASS | `REQ-129D3F`, creator `USR-003`, recipient `ORG-003`, 4 people; PostgreSQL row. |
| 9. NGO opens My Requests and refreshes | PASS | `REQ-129D3F` remains newest-first with stable ID/time and Pending state. |
| 10. Separate Coordinator sign-in opens Requests and refreshes | PASS | Same `REQ-129D3F`, quantity and timestamp, newest-first in the authorized all-request list. |
| 11. PostgreSQL ownership, preserved IDs, ordering, permissions, and benchmark separation | PASS | **28/28** live database/HTTP checks; anonymous resources and NGO admin access rejected. |
| 12. Focused backend regressions and frontend production build | PASS | **18 tests**: 14 dashboard/role/isolation tests plus 4 disaster/allocation tests; TypeScript/Vite build succeeded. Existing bundle-size warning remains. |
| 13. Entire application DB certified free of historical synthetic/ambiguous data | FAIL / intentionally incomplete | Unconfirmed workflows and their connected seed records remain; enumerated above. No authenticity inference from names alone. |
| 14. PostGIS-specific behavior | NOT VERIFIED | This local database has no PostGIS extension. PostgreSQL persistence was verified; the database engine was not changed. |

New verification records are intentionally retained for the requested workflow testing, not represented as real donations:

| Record | PostgreSQL creation time (UTC) | Browser time (Asia/Colombo) |
|---|---|---|
| `RES-5980F3` — VERIFY-20261022-0728 Bread | 2026-10-22 07:25:26.224 | 12:55:26 PM |
| `REQ-129D3F` — VERIFY-20261022-0728 Bread Request | 2026-10-22 07:31:12.768 | 1:01:12 PM |

Their quantities remain 2 kg, reserved/fulfilled quantities remain zero, and their database states remain AVAILABLE/OPEN. Allocation and delivery completion were not repeated on these new cleanup-verification records. The earlier complete delivery/disaster audit remains documented separately in [the role-integration report](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/role-integration-audit-2026-10-22.md); its confirmed disposable operational test records have now been removed, while its evidence files were preserved.

## Review evidence

- [Provider listing and preserved Eggs](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/01-provider-created.png).
- [NGO listing after refresh](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/04-ngo-listing-refresh.png).
- [NGO My Requests after refresh](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/07-my-requests-refresh.png).
- [Coordinator request after refresh](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/09-coordinator-refresh.png).
- [PostgreSQL and live HTTP checks, complete new rows, and counts](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/live-verification.json).
- [14 focused regression results](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/tests.txt), [4 disaster/allocation results](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/disaster-allocation-tests.txt), and [frontend build output](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/frontend-build.txt).
- [Standard benchmark output](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/benchmark-standard.txt) and [advanced benchmark output](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/cleanup-evidence/benchmark-advanced.txt).

The screenshot files listed here were visually inspected. Additional intermediate screenshots are not relied on for PASS claims. The frontend and backend remain running locally in API mode. No push or deployment was performed.
