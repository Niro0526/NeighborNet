# Smart Matching audit and corrected flow

The read-only live audit is in `matching-audit-live.json`; rerun `python audit_matching_state.py` from `backend` to inspect current PostgreSQL records and matching API responses. This audit does not create demand, inventory, recommendations or allocations.

## Findings from actual records

- Nine resource rows and ten NGO request rows existed at inspection. Sixteen normal-mode resource/open-request pairs were screened and rejected; there were no eligible live matches.
- The current bakery request uses `meals`; the bread supply uses `kg` and has closed pickup windows. The newer juice and egg listings do not satisfy the bakery category. Older open requests have expired deadlines.
- No persisted dietary/storage preference fields existed. The profile page also fetched the first organization globally rather than the signed-in user's memberships.
- Screening omitted rejection reasons. Geographic screening used provider-office coordinates rather than food pickup coordinates, and fabricated a 5 km distance for missing coordinates.
- Normal optimization could include disaster demand. Food preference, receiving-hour and custom delivery-location constraints were absent. Courier assignment happened after solving and could leave an apparently feasible plan without a feasible courier.
- Approval and inventory application were separate actions, and application did not recheck the full eligibility criteria. The React page contained hardcoded scenario performance figures.

## Current behavior

The coordinator page at `/admin/matching` displays live inventory, outstanding NGO demand, feasible pairs and rejected pairs with specific reasons. It separates normal and disaster modes. Individual direct food claims remain at `/community-food` and do not become NGO matching demand.

Eligibility uses exact food category and unit consistency, positive remaining quantities, verified organizations, active request creator accounts when recorded, event/mode consistency, pickup windows, request deadlines, safe-consumption deadlines, recorded pickup/delivery coordinates, the existing service radius, and parseable recipient operating/receiving hours in Asia/Colombo. It does not infer dietary properties from names or descriptions, convert meals/liters to kg, geocode address text, or fabricate road travel times.

NGO dietary requirements and storage capabilities are nullable records: null means unknown, and an empty dietary list means explicitly recorded no restrictions. Members can save these through Profile; coordinators can inspect, edit and verify records in Smart Matching. Changes invalidate preference verification. Unverified/unknown preferences are reported, not silently treated as satisfied. Custom delivery addresses require their own coordinates for geographic screening. Unknown/unparseable receiving hours are explicitly reported.

Google OR-Tools CP-SAT solves resource/request/courier decision variables together. Supply and demand are bounded independently. Each selected courier has one mission per plan; a resource/request pair creates one task. Vehicle capacity is measured in kg, and a non-kg listing needs a recorded `unit_weight_kg`. Discrete meals, boxes, packages, kits and items are whole units. Partial demand is allowed only when `allow_partial` is true; otherwise the selected allocations must satisfy the complete remaining request. The objective uses normalized demand fractions, priority, expiry urgency and distance rather than adding unlike units. Metrics conserve stock and demand independently by unit.

Couriers require an active account, approved volunteer role, verified profile, availability, valid coordinates, positive capacity and no active task/direct claim. Non-ambient food needs documented compatible transport storage. Recorded courier speed, when available, screens impossible pickup, receiving and safe-delivery timing; missing speed is explicitly flagged for coordinator review. Distances remain straight-line estimates and do not certify road accessibility or handover time. Coordinator-only `/api/v1/volunteers/{id}/capabilities/` records observed capacity, transport storage and speed.

`POST /api/v1/intelligence/recommendations/{id}/approve/` revalidates and commits the entire plan atomically. It locks the batch and stock/demand/organization/courier rows in stable order, rejects stale or duplicate recommendations, reserves stock, updates demand, creates approved allocations and assigned tasks, writes audit events, and persists notifications for provider, NGO and courier. A failed recheck rolls back the approval and all writes. Repeated approval/application cannot consume inventory twice. Historical approved batches may still use the revalidating apply endpoint. Baseline comparison functions remain for offline evaluation; dispatchable plans use CP-SAT.

The existing PostgreSQL installation has no PostGIS extension available. The distance service uses `ST_DistanceSphere` if PostGIS is enabled and explicitly labeled Haversine distance otherwise. The PostGIS branch has not been executed on this workstation.

## Verification

Tests use real ORM records, Django API endpoints, the installed OR-Tools solver and a separate PostgreSQL test database. No mock recommendations, stock, recipients or API responses are used. Coverage includes preference verification, dietary/storage mismatches, custom locations, unit conversion absence, whole units, partial/full demand, shared courier capacity, stale-plan rollback, competing approvals, source dashboard queries, and the separate personal-claim workflow. Existing NGO receipt/privacy, intelligence, role isolation and disaster tests are included.

Run from `backend`:

```
python -m pytest tests/test_matching_records.py tests/test_intelligence.py tests/test_personal_food_claims.py tests/test_donation_tracking.py tests/test_role_integration_regressions.py tests/test_disasters.py -q
```

Build the React app with `npm run build` from `frontend`.
