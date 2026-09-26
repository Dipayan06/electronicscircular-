# Test Report — Circular Electronics Marketplace

**Framework:** pytest + FastAPI `TestClient` (httpx)
**Environment:** isolated in-memory SQLite (never touches the dev database)
**Result:** **49 / 49 passed** ✅ (33 original + 16 for the Phase 20 enhancements)

Run it:
```bash
cd backend
pytest -q
```

## Strategy

| Level | What it checks | File |
|-------|----------------|------|
| **Unit** | The recommendation engine's rules (pure business logic) | `tests/test_recommendation.py` |
| **API** | Each endpoint's behaviour, auth, validation, status codes | `tests/test_api.py` |
| **Integration** | Complete multi-step workflows end to end | `tests/test_api.py` |

Each test runs against a fresh database seeded with roles + one verified provider, so tests are independent and repeatable.

## Unit tests — Recommendation engine (15)

| Test | Verifies |
|------|----------|
| pristine_device_is_reused | perfect device → REUSE (p2) |
| functional_with_minor_wear_is_resold | minor wear → RESALE (p3) |
| functional_but_old_is_resold | old but working → RESALE |
| single_major_fault_is_repaired | one major fault → REPAIR (p1) |
| not_charging_is_repaired | charging fault → REPAIR |
| two_major_faults_is_refurbished | ≥2 faults → REFURBISH (p4) |
| dead_and_water_damaged_is_recycled | dead + water → RECYCLE (p5) |
| dead_and_old_is_recycled | dead + old → RECYCLE |
| engine_is_deterministic | same input → same output ×50 |
| reason_and_next_step_present | every result is explainable |
| all_actions_are_reachable (×5) | each of the 5 actions is reachable |

## API tests (13)

| Test | Verifies | Req |
|------|----------|-----|
| health | service up | — |
| register_returns_token_and_user | signup issues JWT | AUTH |
| duplicate_email_rejected | 409 on duplicate | AUTH |
| login_success_and_failure | 200 / 401 | AUTH |
| me_requires_auth | 401 without token, 200 with | AUTH |
| password_is_hashed_not_returned | no password leaks in responses | NFR-3 |
| device_crud | create/list/get/update/delete | DEV |
| device_requires_auth | 401 unauthenticated | DEV |
| invalid_device_type_rejected | 422 on bad enum | DEV |
| device_ownership_isolation | user B gets 404 on user A's device | DEV/NFR-3 |
| assessment_returns_recycle_for_dead_device | engine via API → RECYCLE | ASS/REC |
| recommendation_404_before_assessment | 404 when unassessed | REC |
| non_admin_cannot_verify_provider | 403 (RBAC) | FR-K3 |
| admin_role_cannot_be_self_registered | 422 — admin is seed-only | AUTH |

## Integration tests (5)

| Test | Workflow |
|------|----------|
| **full_repair_workflow** | register → device → request quote → provider quotes → accept → book → complete → **lifecycle shows the whole chain** |
| cannot_book_unaccepted_quote | 400 guard: booking requires an accepted quote |
| **full_recycle_workflow** | assess → request collection → SCHEDULED→…→RECYCLED → lifecycle closes the loop; backward move rejected |
| listing_create_and_reserve | list → reserve → 400 on re-reserve |

> Since Phase 20, the helper accounts in these tests register with `@gmail.com`
> addresses (only Gmail/Yahoo may sign up) and are verified through the
> dev-mode code endpoint before listing or buying.

## Phase 20 enhancement tests (16)

| Test | Verifies | Feature |
|------|----------|---------|
| register_rejects_non_allowed_domains | 7 look-alike/other domains → 422; `@yahoo.com` accepted | Email verification |
| new_user_unverified_cannot_list | `is_verified` false after sign-up; listing → 403 | Email verification |
| wrong_code_rejected_then_verify | wrong code → 400; correct code verifies | Email verification |
| notifications_event_driven_and_user_scoped | purchase notifies seller; other user → 404; mark read / mark all read | Notifications |
| prices_labelled_reference_not_live | admin-set price reports `reference`, never `live`; source + timestamp present | Reference pricing |
| only_admin_can_set_reference | consumer → 403; admin edit recorded in history; cache refreshed | Reference pricing |
| invalid_reference_values_rejected | negative price / bad band → 422; refresh without a feed → 400 | Reference pricing |
| price_levels_normal_review_extreme | NORMAL/REVIEW/EXTREME statuses; justification required; g↔kg conversion; per-piece → review; hidden listing 404 to strangers; can't buy while under review | Price regulation |
| non_finite_price_rejected | `NaN` and `0` prices → 422 | Price regulation |
| admin_review_workflow | admin-only queue; approve → ACTIVE, reject → REJECTED; reviewer + note stored; second decision → 409; seller notified | Price regulation |
| estimate_from_purchase_price | ₹50,000, 2 years, Good → ₹23,900 | Resale estimate |
| estimate_falls_back_to_category_reference | no price given → admin typical price, assumed age disclosed | Resale estimate |
| estimate_uses_own_device_assessment_only | cracked screen factor applied; another user's device → 404 | Resale estimate |
| estimate_blends_platform_comparables | 3 comparables blended (60/40); seller's own listings excluded | Resale estimate |
| estimate_unavailable_without_data | "other" with no data → not available; material → 422; no login → 401 | Resale estimate |
| admin_updates_category_reference | consumer → 403; admin edit changes the estimate | Resale estimate |

## Traceability (test IDs → requirements, per RTM §0.12)

Every functional-requirement group has at least one passing test: FR-A (auth),
FR-B (devices), FR-C/FR-D (assessment/recommendation), FR-E (providers/RBAC),
FR-F (quotations), FR-G (bookings), FR-H (marketplace), FR-I (collection),
FR-J (lifecycle). The Phase 20 features (email verification, notifications,
reference pricing, price regulation, resale estimate) each have their own tests
in the table above.

## Frontend testing

The frontend is verified manually against the checklist below (automated React
testing is out of MVP scope). Each was confirmed live in the browser during
development:

- Forms validate and submit (login, register, device, assessment, listing, collection)
- Protected routes redirect when unauthenticated
- Role-aware navigation renders per role
- API errors surface as friendly inline messages / toasts (no raw errors)
- The assessment → recommendation → lifecycle flow renders real backend data
- Phase 20: sign-up domain check and code verification; notification bell
  (unread count, panel, mark read); reference-price labels; price-band feedback
  and admin review; resale estimate on the sell form. All checked on desktop and a
  375px mobile screen

## Defects found & fixed during testing

1. `booking` schema field `date` shadowed the imported `date` type → `datetime.date` (Phase 11).
2. Integration test used a `problem` string shorter than the 3-char minimum → the
   validation guard correctly returned 422; test data corrected.

Both confirm the validation layer is working as intended.
