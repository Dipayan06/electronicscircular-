# HANDOFF — Circular Electronics Marketplace

> **For the next Claude Code session.** Read this first. Updated 2026-09-26.
> This is an existing, working full-stack app. **Extend, don't rebuild.**

## 0. Where things live

- **Project:** `C:\Users\dipay\Desktop\circular-marketplace` (git repo, branch `main`, no remote).
- Not to be confused with `C:\Users\dipay\Desktop\minimal claude` (unrelated "atletico" project). Sessions sometimes open there by mistake.
- **Stack:** React 18 + Vite frontend (pages → service modules → one `apiClient`), FastAPI + SQLAlchemy 2 + Pydantic backend (routers → services → models), SQLite dev / Postgres-ready, JWT auth. Every response uses the `{success, data, message}` envelope.
- **Windows:** backend python is `backend/.venv/Scripts/python.exe`. Stop servers with `taskkill //PID <pid> //F`.
- **Gotcha:** in this shell, Bash heredocs whose content has apostrophes can fail to parse. Use the Write/Edit tools for file content.

### Run
```bash
# backend/ (re-seed after any schema change — it drops + recreates all tables)
.venv/Scripts/python.exe seed.py
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
# frontend/
npm run dev          # http://localhost:5173 (proxies /api → :8000)
# tests
cd backend && .venv/Scripts/python.exe -m pytest -q     # 49 passed
```
Demo logins (seeded, pre-verified): `demo.user@example.com`, `demo.provider@example.com`, `admin@example.com`, all with password `password123`.

## 1. What's done (all committed on `main`)

| Commit | Content |
|---|---|
| `c5e5bc2` | Phase 20 features 1–4: strict email verification (Gmail/Yahoo only, hashed single-use OTP, dev-mode outbox), working notifications (bell, unread count, mark read), material reference pricing (admin-managed, never falsely "Live"), seller price regulation (NORMAL/REVIEW/EXTREME + admin review audit trail) |
| `6380609` | Resale-value estimate on the sell form for devices + components (seller's price or admin category price → age depreciation → condition/assessment → blended with ≥3 platform comparables). Admin → Device pricing tab |
| `374807b` | Phase 20 doc updates: Full Report .docx (new Phase 20 section; cover says Phases 0–20 · 18 tables · 49 tests), TEST_REPORT, DEMO_SCRIPT (Scenario C), VIVA_PREP, deployment.md (new env vars + schema note), READMEs, ENHANCEMENT_REPORT |

Details: `ENHANCEMENT_REPORT.md` (10 sections + addendum). Backend tests: 49 passing (re-run 2026-09-26). 18 tables confirmed from model metadata. Frontend build clean. Everything browser-verified on desktop + 375px mobile.

## 2. Open items

- Full Report .docx nit: the paragraph "The schema now has 18 tables…" has no spacing above it (sits against the table).
- `backend/.env` (git-ignored) now holds a random `JWT_SECRET`. Sharing the app uses a Cloudflare quick tunnel: `cloudflared tunnel --url http://localhost:5173` (the link changes on every restart).
- `.claude/launch.json` has `frontend` and `backend` configs for the desktop app's preview tools.

## 3. State of the environment

- The backend server was stopped by the user at the end of the last session. Vite may still be running on :5173.
- The local DB was re-seeded after the resale-estimate change (includes `category_prices`).

## 4. Known limitations / possible next steps

- No live market feed connected. Seeded material and device-category prices are demo references labelled "not market data". An admin should replace them.
- Existing listings aren't re-checked when a reference price or band changes.
- Notifications are polled every 30 s (could move to SSE/WebSockets).
- Emails compared case-sensitively (pre-existing). Consider normalising to lowercase.
- No migration tool. Add Alembic before production data.
- `EMAIL_DEV_MODE` must be `false` (with SMTP configured) for any real deployment.
- Listing prices are still `Float` (the pricing/review/category tables use `Numeric`).

## 5. Hard constraints (from the original spec)

- All security rules are enforced on the server. Frontend checks are only hints.
- Verification must never be a client-settable boolean.
- No hard-coded secrets (SMTP/API keys only via `.env`).
- Never invent market prices or present reference prices as live.
