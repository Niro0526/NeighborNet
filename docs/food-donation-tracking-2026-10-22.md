# Food Donation Tracking — implementation and live verification

Implemented in the existing Normal Food Rescue dashboards and Django APIs. A verified NGO can accept an eligible offer for its own request; the Provider sees its organization name, quantity, pending/approved allocation, courier assignment, pickup details, delivery state, and a separate NGO receipt milestone. Each allocation has its own timeline, so one completed delivery does not imply that the entire listing has been collected.

The complete workflow was exercised in real browser sessions against React/Vite and Django, backed by PostgreSQL. **One 10 kg listing was split between two NGOs: 4 kg and 3 kg. Both deliveries and both receipts are recorded; 3 kg remains available.** All **61 backend tests**, **35 live PostgreSQL/HTTP verification checks**, and the frontend TypeScript/Vite production build passed.

## What changed

- Provider Overview and My Food reuse a compact donation-tracking section within the existing listing cards. It shows total/allocated/available inventory and separate recipient allocation rows, approval progress, actual courier/pickup information, and expandable seven-step timelines. No dashboard/navigation redesign was performed.
- NGO catalog offers use the existing deterministic eligibility rules against the NGO's own verified, open requests. Accepting a quantity calls the existing atomic allocation endpoint and reserves only that amount, pending Coordinator approval. Stock and outstanding demand are rechecked under PostgreSQL row locks. Quantities are limited to the inventory ledger's two-decimal precision to prevent rounding drift.
- Coordinator Smart Matching / Allocations shows the NGO acceptance approval queue and persists approval timestamps. Pending allocations cannot be claimed as courier missions, including by accounts that combine NGO and Volunteer roles.
- Volunteer delivery actions persist assignment, pickup, arrival, and delivery events. Completed courier deliveries show either the actual receipt timestamp or that NGO confirmation is still pending. A courier's Delivered action does **not** manufacture an NGO receipt.
- The receiving verified NGO has a separate **Confirm Receipt** action after delivery. It stores the authenticated recipient actor and timestamp, emits an audit entry and scoped notifications, and rejects repeats. Provider, Coordinator, other NGOs, and unrelated couriers cannot confirm that NGO's receipt.
- Provider pickup counters now count actual delivery-task handovers, including partial deliveries, instead of counting wholly collected listings. Multi-role NGO accounts no longer count another courier's delivery as their own volunteer completion. Incoming-delivery counters exclude already delivered tasks.
- Historical timestamps are not inferred or backfilled. A missing acceptance, approval, assignment, or receipt date displays **Not recorded**. Unsupported status updates throw errors instead of returning a GET response and displaying a false success. Removed the unrecorded “signed handover” claim and sample facility names; organization names come from Django.
- Profile-loading states no longer imply a courier is available. The account menu has an accessible name even when the responsive layout hides the visible account-name text.

The implemented timeline is:

`Published → NGO Accepted → Coordinator Approved → Volunteer Assigned → Picked Up → Delivered → NGO Receipt Confirmed`

Publication is shared by the listing; subsequent timestamps belong to each individual allocation/task. The new nullable fields are migration `deliveries.0003_donation_tracking_milestones`: allocation acceptance actor/time and approval time, task assignment time, and NGO receipt actor/time. Existing action timestamps and append-only delivery status events remain authoritative for pickup and delivery. Optimizer-created approvals/assignments and courier replacements also record their actual new milestones; legacy records retain nulls where historical evidence is absent.

## Browser-tested records and actors

| Item | Persisted identity |
|---|---|
| Provider | Fathima Rizwan — Perera Grand Catering & Hotel, `ORG-002` |
| Listing | `RES-D5AE00` — `TRACK-20261022 Shared Bread`, 10 kg |
| First NGO | Sister Mary Teresa — Grace Home for the Elderly, `ORG-003` |
| First request / allocation / task | `REQ-DB82FD` / `ALC-873A2F` / `TSK-5FAC09`, 4 kg |
| Second NGO | Anuki Bandara — Suwasetha Child Development Center, `ORG-004` |
| Second request / allocation / task | `REQ-781765` / `ALC-A9E8D9` / `TSK-83489F`, 3 kg |
| Coordinator | Dr. Kaveen Jayawardena |
| Assigned verified courier | Kasun Perera |

Anuki's account has both Recipient and Volunteer roles. Her NGO's receipt was correctly recorded under its NGO membership, while her own courier completion count remained zero. Kasun's two delivered tasks are recorded against his own courier profile.

These explicitly named `TRACK-20261022` records are software-workflow verification data retained for inspection. The test exercised authenticated application actions, not physical food transportation. Existing accounts were reused; no new users or organizations were created.

## Actual milestone times

Browser times below are **22 October 2026, Asia/Colombo**. Full UTC timestamps, actors, raw rows, and HTTP comparisons are in the database evidence JSON.

| Milestone | Grace Home, 4 kg | Suwasetha, 3 kg |
|---|---|---|
| Published | 13:40:27 | 13:40:27 |
| NGO Accepted | 13:42:18 | 13:44:28 |
| Coordinator Approved | 13:47:50 | 13:47:51 |
| Volunteer Assigned | 13:52:16 | 13:59:29 |
| Picked Up | 13:54:31 | 13:59:31 |
| Delivered | 13:56:08 | 13:59:46 |
| NGO Receipt Confirmed | 13:58:49 | 14:00:53 |

Final listing state: **AVAILABLE**, total **10 kg**, allocated **7 kg**, available to allocate **3 kg**. Both allocations are **FULFILLED**, both tasks are **DELIVERED**, and both receipt timestamps are present. Provider totals are **7 kg donated**, **2 recorded pickups**, **0 pending pickups**. Receipt confirmation does not increment the delivery counter again.

## Step-by-step PASS/FAIL report

| Step | Result | Evidence |
|---|---|---|
| Provider publishes 10 kg through React | PASS | `RES-D5AE00`; browser publication capture and PostgreSQL row. |
| Verified first NGO creates its own request and accepts 4 kg | PASS | `REQ-DB82FD`, `ALC-873A2F`; acceptance actor/time persisted; available quantity becomes 6 kg. |
| Provider sees recipient name, accepted quantity, and pending approval | PASS | Provider browser timeline shows NGO Accepted, pending approval, and no invented future dates. |
| Verified second NGO accepts 3 kg from the same listing | PASS | `REQ-781765`, `ALC-A9E8D9`; available quantity becomes 3 kg. |
| Coordinator reviews and approves both allocations separately | PASS | Both IDs appeared in the approval queue and were approved through browser buttons. |
| Verified volunteer claims first approved task | PASS | `TSK-5FAC09`, Kasun assignment actor/event/time; Provider sees actual pickup point/window and courier name. |
| Volunteer records pickup, arrival, and Delivered | PASS | Authenticated browser actions and matching append-only PostgreSQL events. |
| Delivered remains distinct from NGO Receipt Confirmed | PASS | Provider and courier views showed Delivered with receipt still absent before Mary confirmed it. |
| First NGO confirms its own receipt | PASS | Mary confirmed `TSK-5FAC09`; new receipt actor/time persisted and appeared in the courier view. |
| Volunteer completes second task and second NGO confirms receipt | PASS | Kasun delivered `TSK-83489F`; Anuki separately confirmed it. |
| Provider sees both complete timelines after refresh/backend restart | PASS | Both seven-step histories persisted, with 3 kg still available. |
| Provider notification inbox reflects acceptance, approval, pickup, delivery, receipt | PASS | Browser inbox shows both NGO receipts and organization-level event messages. |
| Partial-donation totals are accurate | PASS | Provider browser displays 7 kg and 2 pickups, despite listing remaining AVAILABLE. |
| Multi-role and cross-organization permissions | PASS | Pending NGO allocation could not be claimed as a volunteer mission; wrong-role tracking/receipt access denied; NGO receipt not credited to its own volunteer profile. |
| Recipient privacy | PASS | Private test handling note absent from Provider tracking and request APIs; recipient address/contact redacted from Provider task responses and unassigned courier pool. |
| Repeated receipt and direct state PATCH | PASS | Duplicate receipt rejected with 400; Provider/Coordinator receipt forgery rejected with 403; direct task PATCH rejected with 405. |
| Database/HTTP verification | PASS | 35/35 checks, including exact equality between HTTP timeline dates and PostgreSQL timestamps. |
| Regression/build verification | PASS | Full backend suite: 61 passed; frontend production build passed; `git diff --check` clean. |

The browser also exposed and helped fix the mixed-role pending-mission display and partial-pickup counter defects. Early intermediate captures predate those fixes; final captures and the final regression results are the evidence for the resulting behavior.

## Privacy and permissions

Provider tracking is an explicit allowlist: organization names, quantities, allocation/delivery status, authorized courier name, Provider-owned pickup details, and milestone timestamps. It does not return beneficiary lists, recipient handling instructions, personal receipt-actor details, or recipient delivery addresses/contact numbers. The raw request/task APIs also redact recipient/private information for Provider and unassigned-pool views; the assigned courier and authorized receiving organization retain operational delivery details needed for the task.

Organization notifications are sent to active organization members with approved relevant roles. Receipt notifications are scoped to that Provider, that receiving NGO, assigned courier, and approved Coordinators. The other NGO does not receive the first NGO's private receipt notification; an account that also has an approved Volunteer role can receive the permitted public mission notice. Duplicate event keys protect against repeated inbox entries.

## APIs and implementation locations

- Existing `POST /api/v1/allocations/` now records verified NGO acceptance and pending approval, or an actual Coordinator approval when Coordinator-created.
- `GET /api/v1/allocations/offers/` returns eligible matches for the authenticated NGO's own verified requests.
- Existing `POST /api/v1/allocations/{id}/approve/` records an actual approval timestamp and opens the volunteer pool.
- Existing task acceptance/pickup/delivery endpoints persist the delivery lifecycle.
- `POST /api/v1/delivery-tasks/{id}/confirm_receipt/` records the separate receiving-NGO receipt.
- `GET /api/v1/resources/{id}/tracking/` is restricted to the owning Provider organization or Coordinators and returns real per-allocation history.

Primary implementation files are `backend/apps/deliveries/{models,views,serializers,tracking}.py`, the deliveries migration, resource tracking action, dashboard counts, request privacy serializer, notification fan-out, and the existing optimizer/recovery assignment paths. React reuses the existing Provider/NGO/Coordinator/Volunteer pages with small `DonationTracking`, `AcceptMatchedOffer`, and `PendingDonationApprovals` components.

## Evidence and local environment

- [PostgreSQL rows, actors, events, 35 live checks, and HTTP tracking response](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/database-and-api-evidence.json).
- [Complete Provider timeline after refresh](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/19-provider-second-complete.png) and [complete DOM history](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/19-provider-refresh-dom.txt).
- [Provider final totals](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/20-provider-final-totals.png).
- [Provider Delivered / receipt still pending](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/12-provider-delivered-receipt-pending-dom.txt).
- [Provider notifications](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/18-provider-notifications-dom.txt).
- [Second NGO receipt and multi-role view after refresh](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/16-second-ngo-receipt-refresh-dom.txt).
- [Full backend test output](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/backend-tests.txt) and [frontend build output](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/docs/tracking-evidence/frontend-build.txt).

A pre-migration PostgreSQL backup was created at [before-cleanup.dump](C:/Users/nirov/OneDrive/Desktop/Projects/Neigh/backups/cleanup-20261022-075554/before-cleanup.dump), **163,290 bytes**, SHA-256 `4e67b2c3c27f8c4cdef159ce275965d3fe4ad887a9ecc0aafa2425cfe37bf9e3`; its archive catalog validates. The helper's historical filename does not indicate any deletion in this task. All seven pre-existing listing rows and seven pre-existing request rows match that inventory unchanged. No historical events were fabricated or backfilled. No database reset or record cleanup was performed for this feature.

React remains running in API mode at `http://127.0.0.1:5173`; Django remains running at `http://127.0.0.1:8000`. Existing dashboards and unrelated local changes were preserved. This machine uses PostgreSQL without a PostGIS extension; no PostGIS-specific behavior was changed or claimed as verified. The frontend build retains its existing large-bundle warning. Nothing was pushed, committed, or deployed automatically.
