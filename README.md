# Circular Electronics Marketplace

A working full-stack prototype of a **circular electronics lifecycle platform** —
it helps a consumer give a damaged or unwanted device its *highest-value next
life* (Repair → Reuse → Resale → Refurbish → Recycle) instead of letting it
become e-waste, and records the whole journey as a **Digital Device Passport**.

> Academic Software Engineering project. Not an e-commerce site — a marketplace
> that connects users with repair, resale, refurbishment, collection and
> recycling services, driven by a transparent recommendation engine.

## The core idea

```
Register device → Assess condition → Circularity Recommendation
        ┌───────────────┼───────────────┐
     REPAIR           RESALE          RECYCLE
   find provider    marketplace      collection
   quote → book                       → recycled
        └───────────────┴───────────────┘
                 Digital Lifecycle Record
```

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite, React Router, Axios |
| Backend | FastAPI, SQLAlchemy 2, Pydantic, JWT (python-jose), passlib/bcrypt |
| Database | PostgreSQL (with a zero-setup SQLite fallback for local dev) |
| Tests | pytest + FastAPI TestClient (33 tests) |

## Repository layout

```
circular-marketplace/
├── frontend/      React SPA          (see frontend/README.md)
├── backend/       FastAPI + SQLAlchemy (see backend/README.md)
├── deployment.md  cloud deployment guide
└── README.md      this file
```

## Quick start (local, zero database setup)

**1. Backend** (terminal 1)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
python seed.py                  # creates + seeds circular.db (SQLite)
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
```

**2. Frontend** (terminal 2)
```bash
cd frontend
npm install
copy .env.example .env          # macOS/Linux: cp .env.example .env
npm run dev                     # http://localhost:5173
```

Open **http://localhost:5173** and log in with a demo account.

## Demo accounts (development passwords — change for any real deployment)

| Role | Email | Password |
|------|-------|----------|
| Consumer | demo.user@example.com | password123 |
| Provider | demo.provider@example.com | password123 |
| Admin | admin@example.com | password123 |

## Suggested demo (5 minutes)

1. Log in as the **consumer** → dashboard shows real data.
2. Register a device → **Assess condition** → get a transparent recommendation.
3. **Repair path:** browse providers → request a quote → (log in as **provider**,
   submit the quote) → accept → book → (as provider) mark complete.
4. Open the device's **Digital Passport** — the whole journey is on the timeline.
5. **Recycle path:** assess a dead device → RECYCLE → request collection →
   advance to RECYCLED → the passport closes the loop.

### Enhancement features (see [`ENHANCEMENT_REPORT.md`](ENHANCEMENT_REPORT.md))

6. **Email verification:** register with a `@gmail.com`/`@yahoo.com` address →
   enter the 6-digit code (dev mode: "Show my code" on the verify page).
7. **Notifications:** the bell in the top bar shows unread count; buying,
   quoting, bookings, collections and price reviews all create notifications.
8. **Reference pricing:** Marketplace → *Materials* shows each material's
   reference price with its source and a "not live" label; admins edit them in
   *Admin → Material pricing*.
9. **Price regulation:** sell copper at ₹1,500/kg (2× reference) → a
   justification is required and the listing goes to review; admins approve or
   reject in *Admin → Price reviews*.
10. **Resale estimate:** Sell an Item → Device/Component shows an estimated
    resale range (uses your registered device's assessment, what you paid, and
    similar listings). Admins tune category references in *Admin → Device pricing*.

> After pulling these changes, re-run `python seed.py` — the schema changed
> (new tables: `email_verifications`, `material_prices`,
> `material_price_history`, `price_reviews`; new columns on `users` and
> `notifications`). The seed script drops and recreates all tables.

## Testing

```bash
cd backend && pytest -q      # 49 passed  (see backend/TEST_REPORT.md)
```

## Architecture (layered)

```
React SPA ──REST/JSON──▶ FastAPI ──▶ Services ──▶ SQLAlchemy ──▶ PostgreSQL/SQLite
(pages → service layer)  (routers)   (business    (models)
                                       logic)
```

The **service-layer seam** on both sides means the UI never knew whether data
came from a mock or the real API — which is why the final integration only
touched the service files.

## Security notes

- Passwords are bcrypt-hashed; JWT for stateless auth; role-based authorization.
- All secrets come from `.env` (never committed). `.env.example` documents them.
- ORM-parameterised queries (no SQL injection); CORS restricted to the frontend origin.

## Deployment

See [`deployment.md`](deployment.md) — Render/Railway (backend), Vercel/Netlify
(frontend), a managed PostgreSQL database, and the environment variables to set.
