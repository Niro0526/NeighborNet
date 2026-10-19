# NeighborNet AI — Hard Constraints & Matching Rules

## 1. Deterministic Screening Pipeline

Before candidates enter any optimization or baseline allocation algorithm, they must pass 100% of the following hard constraints in `backend/apps/intelligence/services/eligibility.py`:

```
Candidate Resource Lot + Recipient Request
                    │
                    ▼
       [1. Expiry Deadline Check] ------------> Fail -> INELIGIBLE (Expired)
                    │ Pass
                    ▼
       [2. Food Safety Guidelines] -----------> Fail -> INELIGIBLE (Unsafe/Unknown)
                    │ Pass
                    ▼
       [3. Organization Verification] --------> Fail -> INELIGIBLE (Unverified)
                    │ Pass
                    ▼
       [4. Category Compatibility Matrix] ----> Fail -> INELIGIBLE (Incompatible)
                    │ Pass
                    ▼
       [5. Operating Mode Alignment] ---------> Fail -> INELIGIBLE (Mode Mismatch)
                    │ Pass
                    ▼
       [6. Spatial Service Radius < 35km] ----> Fail -> INELIGIBLE (Out of Range)
                    │ Pass
                    ▼
       [7. Time Window Overlap] --------------> Fail -> INELIGIBLE (Timing Window)
                    │ Pass
                    ▼
         ELIGIBLE CANDIDATE PAIR
```

---

## 2. Detailed Constraint Definitions

### Constraint 1: Expiry Deadline
- **Rule:** `resource.use_by > timezone.now() + timedelta(hours=2)`
- **Rationale:** Food lots must have at least 2 hours of viable shelf life remaining to allow sufficient transit time for collection and delivery.

### Constraint 2: Food Safety Guidelines
- **Rule:** `resource.food_safety_details` must be non-empty and specify safe storage/handling.
- **Strict Prohibition:** Unknown or missing food safety information is never treated as safe. Machine learning or LLM hallucinations are never used to assess food safety.

### Constraint 3: Organization Verification
- **Rule:** `resource.donor.is_verified is True` AND `request.recipient.is_verified is True`.
- **Rationale:** Ensures only vetted institutions participate in surplus distribution.

### Constraint 4: Category Compatibility Matrix
Compatibility is governed by an explicit deterministic map:
- `prepared_meals`: Compatible with `prepared_meals` requests.
- `bakery`: Compatible with `bakery` and `canned_dry_goods`.
- `fresh_produce`: Compatible with `fresh_produce` and `drinking_water` / relief packs.
- `dairy_perishables`: Compatible with `dairy_perishables`.
- `canned_dry_goods`: Compatible with `canned_dry_goods` and emergency packs.
- `emergency_supplies`: Compatible with `drinking_water`, `hygiene_kits`, `blankets_bedding`.

### Constraint 5: Operating Mode & Disaster Alignment
- In **Normal Mode**: Disaster-specific emergency requests are excluded.
- In **Disaster Mode**: Requests must be associated with an active `DisasterEvent`.

### Constraint 6: Service Area Proximity
- Straight-line Haversine distance between donor coordinates and recipient coordinates must not exceed 35.0 km (covering the Moratuwa, Ratmalana, and Greater Colombo South area).
