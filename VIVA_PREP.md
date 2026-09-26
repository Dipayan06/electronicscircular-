# SWE Viva Preparation — Circular Electronics Marketplace

Everything you need to defend the project: the pitch, how it was built, likely
questions with crisp answers, the artifact index, and honest limitations.

---

## 1. The 30-second pitch

> "The electronics ecosystem is fragmented — repair, resale and recycling operate
> separately, so people don't know the best next step for a broken device. We
> built a **circular electronics marketplace**: the user registers a device,
> describes its condition, and a transparent rule-based engine recommends its
> highest-value next life — repair, reuse, resale, refurbish or recycle — then
> connects them to the right service. Every step is recorded in a **Digital
> Device Passport**. It's a full-stack prototype: React frontend, FastAPI
> backend, SQLAlchemy + a relational database, JWT auth, and automated tests."

---

## 2. "How did you actually build it?" (the methodology)

We followed a **phased software-engineering process**, not big-bang coding:

1. **Requirements** (Phase 0) — problem, actors, functional/non-functional
   requirements, use cases, a requirements traceability matrix.
2. **Design** (Phases 1–2) — layered architecture, DFDs, UI/UX wireframes, the
   component hierarchy.
3. **Frontend foundation & functionality** (Phases 3–4) — a runnable React shell,
   then every screen against a clearly-labelled **mock service layer**.
4. **Database & backend** (Phases 5–7) — the normalized schema + SQLAlchemy
   models, the FastAPI app with Swagger, then JWT authentication.
5. **Feature build-out** (Phases 8–13) — devices, the recommendation engine,
   providers/marketplace, quotations/bookings, collection/recycling, the
   lifecycle passport — each built and tested on the backend.
6. **Integration & hardening** (Phases 14–17) — swapped the frontend from mock to
   the real API in one cut-over, hardened error handling, added automated tests,
   prepared deployment.
7. **Delivery** (Phases 18–19) — a rehearsed demo and this viva prep.
8. **Enhancements** (Phase 20) — verified sign-up, working notifications,
   material reference pricing, seller price regulation, and resale-value
   estimates, added on top of the working system without changing any existing
   workflow (details in `ENHANCEMENT_REPORT.md`).

**Why mock first, then swap?** The frontend was built against a service-layer
seam, so pages never knew if data came from a mock or the API. That let us build
and demo the UI early, then integrate everything at once (Phase 14) without
inconsistent half-states. It's the payoff of separating concerns.

---

## 3. Q&A by topic

### Process
**Q: How did you manage the development?**
> Phase by phase, with a documentation artifact at each step. Requirements drove
> the design, the design drove the database and backend, and the traceability
> matrix kept them consistent.

**Q: What was the hardest part?**
> Integration. Because a quotation references both a device and a provider,
> swapping the frontend to the real backend one domain at a time would break the
> links. We built all the backend endpoints first, then did a single coordinated
> cut-over — which the service-layer design made a localized change.

### Architecture
**Q: Describe the architecture.**
> A layered client–server system. React SPA (presentation) talks to FastAPI over
> REST/JSON. The backend has an API layer (routers), a business-logic layer
> (services), and a data-access layer (SQLAlchemy models) over the database.
> Dependencies point downward only, so each layer has one responsibility.

**Q: Why separate routers and services?**
> Routers handle HTTP — parse the request, check auth, shape the response. All the
> rules live in services. That keeps handlers thin, makes the logic testable
> without HTTP, and means the recommendation engine, for example, is a plain
> function we can unit-test.

### Frontend (React)
**Q: What is React and why use it?**
> A component-based UI library. We use it for reusable components (DeviceCard,
> LifecycleTimeline, StatusBadge), client-side routing, and a single Axios client
> that is the only place HTTP is called.

**Q: How does the frontend talk to the backend?**
> Through service modules that call a shared Axios instance. It attaches the JWT
> automatically and unwraps our standard `{success, data, message}` envelope.

### Backend (FastAPI)
**Q: What is FastAPI and what's the advantage?**
> A Python web framework. It validates requests with Pydantic and auto-generates
> interactive Swagger docs at `/docs`, which we can use to demo the API directly
> against the database.

**Q: What is an ORM / SQLAlchemy?**
> An Object-Relational Mapper — Python classes map to tables, objects to rows. We
> work with objects; SQLAlchemy generates safe, parameterised SQL, which also
> prevents SQL injection.

### Database
**Q: Walk me through the schema.**
> 13 normalized tables. A user owns many devices; a device has assessments,
> quotations, bookings, collection requests, and lifecycle events. A quotation
> maps to at most one booking (a unique foreign key). Provider services were
> normalized into their own table instead of a list column.

**Q: SQLite or PostgreSQL?**
> Both — we develop on SQLite for zero setup, but the code is PostgreSQL-ready.
> Because we used an ORM, switching is a one-line connection-string change.

### Authentication & security
**Q: How does authentication work?**
> On login we verify a bcrypt password hash and issue a signed JWT containing the
> user id and role. The client sends it as a Bearer token; the server verifies it
> on each request. It's stateless — no server session.

**Q: Authentication vs authorization?**
> Authentication is *who you are* — the JWT. Authorization is *what you may do* —
> we check the role in the token. For example, only an admin can verify a
> provider; a normal user gets a 403.

**Q: How do you keep passwords safe?**
> We never store them. bcrypt hashes each one with a salt; we store only the hash
> and compare hashes at login.

**Q: How is data kept private between users?**
> Every query is scoped by the user id from the JWT, never from the request body.
> Asking for another user's device returns 404 — proven by a test.

### The recommendation engine (the centrepiece)
**Q: Is the recommendation AI?**
> No — and that's deliberate. It's a **rule-based engine**: transparent, ordered
> rules over the assessment inputs. No model, no training data, no randomness. The
> same input always gives the same output, so we can explain and unit-test every
> recommendation. AI grading is listed as future work.

**Q: Give an example rule.**
> If a device won't power on and is water-damaged or very old, it's not
> economically repairable, so we recommend RECYCLE. If it's fully working with only
> minor wear, we recommend RESALE — the engine always prefers the highest-value
> option on the circularity ladder.

### Phase 20 enhancements
**Q: How do you stop fake or throwaway accounts?**
> Only Gmail and Yahoo addresses can register, and the server enforces it (the
> form check is just a hint). A 6-digit code is emailed; we store only its bcrypt
> hash, it expires in 10 minutes, it can be used once, and five wrong tries burn
> it. Resends are rate-limited. The "verified" flag can only be set by a correct
> code, and selling or buying needs a verified account.

**Q: Why doesn't the verification email arrive in the demo?**
> Development mode: there's no mail server, so the code goes to a local outbox and
> the account owner can reveal their own code. Setting the SMTP variables sends
> real email. Production must turn dev mode off.

**Q: How do notifications work?**
> One service writes a notification inside the same database transaction as the
> event (a purchase, a quote, a booking change, a price decision), so they're
> always consistent. The bell checks the unread count every 30 seconds. Every
> query is scoped to the logged-in user, so nobody can read or mark someone
> else's.

**Q: Where do the material prices come from? Are they live?**
> Not unless a live market feed is connected. Without one, prices are set by an
> admin and labelled "Reference · not live" with their source and date. A price
> is only called "Live" if it came from the feed and is fresh; old ones are
> marked "Stale". If the feed fails we keep the last known value and its
> original date, so it ages visibly instead of pretending to be current. Money is
> stored as exact decimals, not floats.

**Q: How do you stop sellers overcharging?**
> When a material is listed, the server compares its price per gram with the
> reference. Between 0.5× and 1.5× it goes live. Outside that, up to 3×, the
> seller must justify it and an admin reviews it; buyers can see it but can't
> buy it. Above 3× it's hidden until reviewed. Suspiciously cheap prices are
> reviewed too (fraud signal). Switching to "per piece" to dodge the check sends
> it to review, and NaN or negative prices are rejected. Each review keeps a
> snapshot of the numbers, the reason, and who decided, when and why.

**Q: How does the resale estimate work? Is it AI?**
> No, it's a transparent formula, like the recommendation engine. It starts from
> what the seller paid (or an admin-set typical new price), removes a yearly
> percentage for age, applies the assessment's faults (a cracked screen keeps
> 60%, water damage 50%), and blends in similar listings when there are at least
> three. It shows every step and a confidence level, and if there's no data it
> says so instead of guessing.

### Testing
**Q: How did you test it?**
> 49 automated tests: unit tests for the engine, API tests for each endpoint
> (auth, validation, ownership, RBAC), integration tests that run the whole
> repair and recycle journeys, and 16 tests for the Phase 20 features. Each uses
> an isolated in-memory database.

**Q: Did testing find bugs?**
> Yes — a schema field-shadowing bug, and a validation guard correctly rejecting
> bad test input. Finding issues is exactly what tests are for.

### Deployment
**Q: How would you deploy this?**
> Frontend to Vercel/Netlify, backend to Render/Railway, a managed PostgreSQL
> database. All secrets come from environment variables; nothing sensitive is in
> Git. It's documented in `deployment.md`.

---

## 4. Artifact index (brief §42) — what & where

| # | Artifact | Where |
|---|----------|-------|
| 1–3 | Problem, objectives, feasibility | Phase 0 |
| 4–7 | SRS, functional/non-functional reqs, user stories | Phase 0 |
| 8–10 | Use cases, use-case descriptions, activity diagrams | Phase 0 / Phase 2 flows |
| 11–12 | DFD Level 0 & 1 | Phase 1 |
| 13 | ER diagram | Phase 5 |
| 14–15 | Class diagram, sequence diagrams | Phase 1/5 (models) + Phase 11 flow |
| 16–17 | Component & deployment diagrams | Phase 1 / `deployment.md` |
| 18 | System architecture | Phase 1 |
| 19 | Database schema | `backend/app/models/` + Phase 5 |
| 20 | API documentation | Swagger `/docs` (live) |
| 21 | UI wireframes | Phase 2 |
| 22–24 | Test plan, cases, report | `backend/TEST_REPORT.md` |
| 25 | Deployment documentation | `deployment.md` |
| 26 | User manual | `README.md` + `DEMO_SCRIPT.md` |
| 27 | Developer documentation | `README.md`, `frontend/README.md`, `backend/README.md` |
| — | Enhancement report (Phase 20) | `ENHANCEMENT_REPORT.md` + Phase 20 in the Full Report |

---

## 5. Facts worth memorising

- **5 circular actions:** Repair (1) · Reuse (2) · Resale (3) · Refurbish (4) · Recycle (5)
- **6 roles:** consumer, provider, refurbisher, recycler, supplier, admin
- **18 database tables**, **49 passing tests** (13 tables and 33 tests before Phase 20)
- **Price bands:** 0.5×–1.5× NORMAL · up to 3× REVIEW · above 3× EXTREME (admin-configurable)
- **Verification code:** 6 digits · bcrypt-hashed · 10 min · single-use · 5 attempts
- **Stack:** React + Vite · FastAPI + SQLAlchemy + Pydantic · PostgreSQL/SQLite · JWT
- **Two signature features:** the rule-based recommendation engine, and the Digital Device Passport (append-only lifecycle timeline)
- **Scope:** smartphones, laptops, tablets. **Out of scope (future):** AI grading, IoT, real payments.

---

## 6. Honest limitations & future work (if asked "what would you improve?")

- **AI-based grading** from photos — currently a transparent rule engine (by design for the MVP).
- **Real payments** — resale/reservation is simulated; no payment gateway.
- **IoT device tracking** — future enhancement.
- **Notifications** — working in-app notifications, but checked every 30 s rather than pushed; no SMS/push delivery.
- **Live market prices** — no market feed connected yet; material and device-category prices are admin references (labelled "not market data").
- **Existing listings aren't re-checked** when a reference price changes (regulation applies when a listing is created).
- **No migration tool** — the seed recreates tables; add Alembic before production data.
- **Frontend automated tests** — manual checklist for the MVP; would add React Testing Library.
- **One role per account** — a simplification; a real system might allow multiple roles per user.

Framing them as *deliberate MVP scope decisions with a clear upgrade path* is
stronger than treating them as gaps.

---

## 7. If you get stuck on a question

- Point to the **architecture diagram** and walk the request path.
- Open **Swagger** and run an endpoint live.
- Open the **Digital Passport** — it visually tells the whole story.
- Run **`pytest -q`** — 49 passing tests answer a lot of doubts at once.
