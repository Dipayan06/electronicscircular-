# Enhancement Report: Marketplace Features (Phase 20)

**Project:** Circular Electronics Marketplace · **Date:** 26 September 2026
**Scope:** Four features added to the existing working app (Phases 0–19), plus a
resale-value estimate (see the addendum at the end). Nothing
was rebuilt: every existing screen, API, workflow and style is kept.

---

## 1. Summary

| # | Feature | Outcome |
|---|---------|---------|
| 1 | Strict email verification | Only `@gmail.com` / `@yahoo.com` can register (checked on the server). A hashed, single-use, expiring 6-digit OTP must be verified before a user can sell or buy. |
| 2 | Material reference pricing | A `MaterialPrice` table with exact `Numeric` money, source, currency, unit and timestamps. Admins manage the values. An optional market feed can be plugged in. The UI never labels a price "Live" unless it really is. |
| 3 | Working notifications | The static bell now shows an unread count, a dropdown panel, per-item and mark-all read, and per-user persistence. Real marketplace events create the notifications. |
| 4 | Seller price regulation | Every material listing price is classified on the server as NORMAL / REVIEW / EXTREME against an admin-set band. Flagged listings go through an admin review workflow with a full audit trail. |

Backend tests went from 33 to **43 passing**. The frontend production build is
clean. All four features were also checked by hand in the browser, on desktop
and mobile layouts.

## 2. Architecture and design decisions

The existing layers are unchanged: **routers (HTTP) → services (business logic)
→ models (SQLAlchemy)** on the backend, and **pages → service modules →
`apiClient`** on the frontend. Every response still uses the `{success, data,
message}` envelope through `APIError` and the global exception handlers.

Key decisions:

- **The server is the only trust boundary.** Domain checks, verification state,
  price classification and review decisions are all computed on the server. The
  frontend repeats some checks only to give faster feedback (domain hint, live
  price-band preview).
- **Honest pricing over convenient pricing.** No market price is invented.
  With no feed configured, prices are admin-set *references*. They are labelled
  that way everywhere, with their source and age.
- **One notification writer.** `notification_service.notify(..., commit=False)`
  joins the caller's transaction, so a notification is saved exactly when the
  business event it describes is saved.
- **Review snapshots.** A `PriceReview` stores the reference price and ratio used
  at decision time, so later price changes don't rewrite history.

## 3. Feature 1: Strict email verification

**Rules.** Registration accepts only `gmail.com` and `yahoo.com`, compared as an
exact domain match. That rejects `hotmail.com`, `outlook.com`,
`protonmail.com`, `gmail.co`, `yahoo.co.in`, `mail.gmail.com`, company
domains, and so on. The rule is enforced twice on the server: in the Pydantic
schema and again in `auth_service.assert_allowed_domain`. Login is not
domain-restricted, so the seeded demo `@example.com` accounts still work.

**OTP lifecycle** (`app/services/auth_service.py`, `app/models/verification.py`):

- Codes are 6 digits from `secrets.randbelow` and stored **only as a bcrypt
  hash**. The plaintext is never saved to the database or written to logs.
- Codes expire after 10 minutes (`OTP_TTL_MINUTES`) and are single-use via the
  `consumed` flag. Issuing a new code invalidates the old one.
- After 5 wrong attempts the code is burned (HTTP 429).
- Resends have a 60-second cooldown and a cap of 5 per hour (HTTP 429).
- `users.is_verified` can only become true through a successful OTP check. No
  endpoint lets a client set it.
- `require_verified` guards creating listings and buying/reserving (HTTP 403 if
  the user is not verified).

**Delivery.** In dev mode (the default) no mail server is used. The message goes
to `backend/data/dev_outbox/` (gitignored), and the logged-in owner can fetch
**their own** pending code from `GET /api/auth/dev/verification-code`. That
endpoint returns 404 when `EMAIL_DEV_MODE=false`. Setting `SMTP_*` switches
delivery to real email over STARTTLS.

**UI.** The register form shows a domain hint and sends users to
`/verify-email` after signing up. That page has code entry, resend, and "Show
my code" in dev mode. A banner in the app shell reminds unverified users.

## 4. Feature 2: Material reference pricing

**Model** (`app/models/pricing.py`). `MaterialPrice` holds one row per material:
rare-earth, gold, silicon, copper, aluminium. Each row stores:

- `reference_price` as `Numeric(14,4)`, never a float
- `currency` and `unit`
- `source` (readable provenance) and `source_type` (`admin` | `api`)
- `observed_at` (when the price was true at the source) and `updated_at` (last
  write)
- `last_fetch_error`
- the Feature 4 band multipliers

`MaterialPriceHistory` is an append-only log of every change.

**Status labels.** These are computed on each read, never stored:

- `live`: came from the feed **and** is younger than `PRICE_STALE_AFTER_HOURS`
- `reference`: set by an admin, within the freshness window. Shown as
  "Reference · not live".
- `stale`: older than the window. Shown as "Stale · not live".

**Caching and failures.** The public price list is cached in memory for 60
seconds, and any write clears the cache. `POST /api/pricing/refresh` pulls from
the feed if `PRICE_API_BASE_URL` is set. If a material fails, its last-known
value **and its original timestamp** are kept, so it ages into `stale` instead
of passing as current. The error is saved on the row and shown to admins. With
no feed configured, refresh returns a clear 400 and the admin button is
disabled.

**Seed values.** The seed data holds demo references, labelled *"Admin
reference — demo seed value, not market data"*. The app never presents them as
market prices.

**UI.** A reusable `PriceReferenceTag` shows the price, a status pill, the
source and the age. It appears on:

- material listing detail pages
- the sell form
- a "Material reference prices" strip on the Marketplace → Materials tab
- **Admin → Material pricing**, which adds editing (price, unit, source note,
  band), per-material history, and "Refresh from feed"

## 5. Feature 3: Notifications

**Model.** The existing but unused `notifications` table was extended with
`type`, `title`, `message`, `read`, `read_at`, `metadata` (JSON) and
`created_at`, indexed by `user_id`.

**Events that create notifications:**

| Event | Recipient |
|-------|-----------|
| Listing bought/reserved | Seller ("New order received") and buyer ("Purchase confirmed") |
| Quote requested / submitted / accepted or rejected | Provider / device owner / provider |
| Booking status changed | Device owner |
| Collection advanced | Device owner |
| Email verified | The user |
| Listing flagged by price regulation | All admins |
| Price review approved / rejected | Seller |

**API.** `GET /api/notifications` (latest 50 plus unread count),
`GET /unread-count`, `PUT /{id}/read`, `PUT /read-all`. Every query filters by
the authenticated user. Marking someone else's notification returns 404, so no
IDOR is possible.

**UI.** `NotificationBell` replaces the static icon in the top bar:

- Unread badge, with the count polled every 30 seconds (paused while the tab is
  hidden).
- Clicking the bell opens a panel of recent notifications; unread items are
  highlighted and a "Mark all read" button is available.
- Clicking an item marks it read and jumps to the related listing when there is
  one.
- On mobile the panel becomes a full-width sheet. The logout menu is unchanged.

## 6. Feature 4: Seller price regulation

**Classification** (`pricing_service.assess_price`). The listing price and the
reference price are both converted to price per gram (`g`/`kg`/`tonne`), then
compared as a ratio against the material's admin-set band. The defaults are:

| Ratio vs reference | Level | Listing status | Visibility |
|---|---|---|---|
| `band_min` (0.5×) to `band_max` (1.5×) | NORMAL | `ACTIVE` | Public, can be bought |
| Below 0.5×, or 1.5× up to 3× | REVIEW | `PRICE_REVIEW_REQUIRED` | Public with a badge; **cannot be bought** |
| Above `extreme_max` (3×) | EXTREME | `SUSPENDED_PENDING_REVIEW` | **Hidden** from the marketplace and from direct id lookups by strangers |

- A REVIEW price **requires a seller justification** of at least 10 characters,
  or the API returns 422.
- Unusually *low* prices are also reviewed, as a fraud signal.
- A listing priced per `piece` can't be compared by mass, so it goes to REVIEW.
  This stops sellers from dodging regulation by switching units.
- Devices, components and "other" have no reference price and are not
  regulated.

**Anti-bypass measures:**

- Prices must be positive, finite (NaN and Infinity are rejected) and at most
  1e9.
- The level is always recomputed on the server. The `/pricing/check` preview is
  advisory only.
- The seller is always the authenticated user.
- Hidden listings return 404 to anyone except the seller and admins.
- There is no endpoint for editing prices, so a price can't be changed after
  approval.

**Review workflow** (`price_review_service`, `/api/price-reviews`). Each
flagged listing gets a `PriceReview` row. The row snapshots the listed price,
the reference price, the ratio and the reason, and stores the seller's
justification.

- Admins are notified when a review opens.
- Approve sets the listing to `ACTIVE`; reject sets it to `REJECTED`.
- The reviewer, time and note are saved on the row, and the seller is notified.
- Decisions are final: deciding twice returns 409.
- Sellers can see only their own reviews (`/price-reviews/mine`). The admin
  list and decision endpoints are admin-only.

**UI:**

- The sell form shows a live band preview with the reason, plus a justification
  box when needed.
- After submitting, the seller lands on the listing, which explains the held
  status, the reason and any admin note.
- The Marketplace has a "My listings" filter that includes held items.
- **Admin → Price reviews** lists reviews with status filters and approve/reject
  buttons, each with an optional note.

## 7. Data model and migration

New tables: `email_verifications`, `material_prices`, `material_price_history`,
`price_reviews`.

Changed tables:

- `users` gains `is_verified`.
- `notifications` columns are rewritten.
- `resale_listings.status` allows three new values.

The project has no migration tool. `seed.py` drops and recreates every table,
so **run `python seed.py` after pulling**. For PostgreSQL, add Alembic before
running this against real data. `Base.metadata.create_all` creates new tables
but does not alter existing ones.

The seed data now also includes:

- five reference prices, with history
- one REVIEW listing and one EXTREME listing, each with a pending review
- demo notifications for the consumer, provider and admin

## 8. API reference (new and changed endpoints)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/verify-email` | user | Submit the OTP |
| POST | `/api/auth/resend-verification` | user | New code (rate-limited) |
| GET | `/api/auth/dev/verification-code` | user, dev mode only | Own pending code |
| GET | `/api/notifications` | user | Items plus unread count |
| GET | `/api/notifications/unread-count` | user | Unread count |
| PUT | `/api/notifications/{id}/read` · `/read-all` | user | Mark read |
| GET | `/api/pricing/materials` · `/{material}` · `/{material}/history` | public | Reference prices and history |
| PUT | `/api/pricing/materials/{material}` | admin | Set price and/or band |
| POST | `/api/pricing/refresh` | admin | Pull from the market feed |
| POST | `/api/pricing/check` | user | Preview a price's level |
| GET | `/api/price-reviews?status=` | admin | Review queue |
| GET | `/api/price-reviews/mine` | user | Own reviews |
| PUT | `/api/price-reviews/{id}/approve` · `/reject` | admin | Decide, with an optional note |
| GET | `/api/listings/mine` | user | Own listings, including held ones |
| POST | `/api/listings` | **verified** user | Now classifies the price. Takes `price_justification`; returns `price_assessment`. |
| PUT | `/api/listings/{id}/reserve` | **verified** user | Rejects listings under review |
| GET | `/api/listings` · `/{id}` | public | Hides suspended and rejected listings (the seller and admins can still open them by id) |

New environment variables, documented in `backend/.env.example`:
`EMAIL_DEV_MODE`, `EMAIL_FROM`, `SMTP_*`, `OTP_*`, `RESEND_*`,
`PRICE_API_BASE_URL`, `PRICE_API_KEY`, `PRICE_STALE_AFTER_HOURS`. No secrets
are committed.

## 9. Security review and test results

**Security checklist:**

- **Server-side enforcement:** covers domain, verification, price level, roles
  and review decisions.
- **No client-settable verification:** `is_verified` changes only through the
  OTP check.
- **OTPs:** hashed, expiring, single-use and attempt-limited, with resends
  rate-limited. Dev codes are available only to the account owner and only in
  dev mode.
- **IDOR/BOLA:** notifications, reviews and hidden listings are all scoped to
  the user; other users get 404.
- **Admin-only mutations:** pricing and reviews use `require_role("admin")`.
- **Input hardening:** non-finite and non-positive prices and bands are
  rejected, and money math uses `Decimal`.
- **Secrets:** SMTP and feed keys are read only from `.env`, and the feed key
  is never logged or returned. The dev outbox directory is gitignored.

**Automated tests.** `cd backend && pytest -q` gives **43 passed**. Ten new
tests cover:

- domain rejection (7 bad domains) and acceptance
- unverified users blocked from listing
- wrong-code rejection, then successful verification
- event-driven notifications, including IDOR and read-state checks
- reference prices labelled "reference", not "live"
- admin-only price edits, history, and cache invalidation
- invalid price and band values, plus refresh without a feed
- all three price levels, including unit conversion, piece-unit anti-bypass,
  public visibility and buy blocking
- NaN and zero prices rejected
- the full approve and reject workflow with notifications, and 409 on a second
  decision

Existing tests were updated to register `@gmail.com` addresses and to verify
users before listing.

**Manual browser checks** (Vite + live API):

- Register with outlook.com → rejected. With gmail.com → verify page.
- Wrong code → "Incorrect verification code". Dev code → verified, and the bell
  shows 1.
- Selling copper at ₹1,500/kg shows "Price needs review" and requires a
  justification. The listing is held, with its reason shown.
- The admin sees 3 pending reviews and 2 notifications, approves with a note,
  and the queue updates.
- The admin edits copper to ₹800/kg: the source note is saved and the price is
  still labelled "not live".
- On a 375px mobile viewport, the bell panel fits the screen, there is no
  horizontal scroll, and the logout menu is intact.
- No unexpected console errors.

`npm run build` succeeds. Its chunk-size warning was there before these
changes.

## 10. Limitations and future work

- **No live market feed is connected.** The adapter
  (`pricing_service._fetch_from_feed`) is generic and must be adapted to a
  chosen provider (for example MCX/LME data). Until then, all prices are admin
  references.
- **Existing listings are not re-checked** when a reference price or band
  changes. Regulation applies at creation time. A future job could re-assess
  active listings.
- **Listing prices stay `Float`** for compatibility with existing screens.
  Only the pricing and review tables use `Numeric`. Moving listings to
  `Numeric` is a contained follow-up.
- **Notifications are polled** every 30 seconds rather than pushed. SSE or
  WebSockets would make them instant.
- **Emails are compared case-sensitively** (unchanged from before).
  Normalising to lowercase at registration and login is recommended.
- **No migration tool.** Adopt Alembic before running against production data.
- **Dev-mode OTP delivery** writes codes to a local outbox file by design. Turn
  it off (`EMAIL_DEV_MODE=false` plus SMTP) for any real deployment.

---

## Addendum: Resale-value estimate (devices and components)

When a seller lists a device or component, the sell form now shows an
**estimated resale range** with a suggested price and a "Use this price"
button. The estimate is deterministic and explains itself. It is never
presented as a market quote.

**How the number is built** (`backend/app/services/valuation_service.py`):

1. **Anchor.** The price the seller paid, if they enter it. Otherwise the
   admin-set *typical new price* for the category (`category_prices` table,
   `Numeric` money, labelled as an admin reference). If neither is available
   and there are too few comparables, the app says so instead of guessing.
2. **Age.** The anchor loses a fixed share of its value each year, set per
   category (for example smartphones 25%/year, CPUs 15%/year), down to a
   minimum value. The age comes from the registered device or the "year
   bought" field. If it's unknown, 2 years is assumed and the seller is told.
3. **Condition.** For a registered device with an assessment, the answers
   drive the multiplier. For example, a cracked screen keeps 60% of the value,
   a weak battery 90%, water damage 50%, and a device that won't power on
   30%. Otherwise the listing condition is used (Excellent 1.0, Good 0.85,
   Fair 0.7, Refurbished 0.9, For parts 0.25).
4. **Platform comparables.** With at least 3 similar listings (same kind and
   category, last 180 days, ACTIVE/RESERVED/SOLD, excluding the seller's own
   listings), the result is 60% formula and 40% comparable median.
   Same-brand listings are preferred when there are enough.
5. **Range and confidence.** The range is ±12%, ±18% or ±28%, depending on
   whether a purchase price, a known age and comparables are all present.

The purchase price is used only for the estimate and is not stored.
Estimating from a `device_id` works only on the caller's own device (404
otherwise).

**API.**
- `POST /api/valuation/estimate` (logged-in user)
- `GET /api/valuation/categories` (public)
- `PUT /api/valuation/categories/{category}` (admin)

**Admin.** The new **Admin → Device pricing** tab edits each category's
typical new price (with a source note), yearly value loss and minimum value.
The seed values are demo references labelled *not market data*.

**Tests.** 6 new tests (49 passing in total):
- the purchase-price formula
- the category fallback with assumed age
- assessment factors and device ownership
- comparable blending and self-exclusion
- the not-available case and input errors
- admin-only category edits flowing through to the estimate

Checked in the browser: a Dell XPS (paid ₹95,000, bought 2021, minor screen
wear and weak battery) is estimated at ₹25,200, matching the hand calculation.
The GPU fallback gives ₹20,000. The mobile layout fits with no horizontal
scroll.
