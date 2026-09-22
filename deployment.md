# Deployment Guide

The prototype runs locally with zero setup (SQLite). This guide covers deploying
the same code to the cloud with a real PostgreSQL database. Deployment is
**optional** for the academic demo — the architecture is deploy-ready.

```
Vercel / Netlify  ──HTTPS──▶  Render / Railway  ──▶  Managed PostgreSQL
(React build)                 (FastAPI/Uvicorn)       (cloud database)
```

## 1. Database — Managed PostgreSQL

Create a PostgreSQL instance on any provider (Render, Railway, Neon, Supabase,
ElephantSQL). Copy its connection URL, e.g.:

```
postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
```

> Note the `+psycopg2` driver prefix — SQLAlchemy needs it.

## 2. Backend — Render / Railway

1. Point the service at the `backend/` directory.
2. Install the PostgreSQL driver: uncomment `psycopg2-binary` in
   `requirements.txt` (or `pip install psycopg2-binary`).
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables (see table below).
6. Seed once (from a one-off shell / job): `python seed.py`
   — or remove the demo seed for a real deployment.

### Backend environment variables

| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+psycopg2://…` | the managed Postgres URL |
| `JWT_SECRET` | a long random string | **must** be strong & secret in prod |
| `JWT_EXPIRE_MINUTES` | `120` | token lifetime |
| `FRONTEND_ORIGIN` | `https://your-app.vercel.app` | CORS allow-list (exact origin) |

## 3. Frontend — Vercel / Netlify

1. Point at the `frontend/` directory.
2. **Build command:** `npm run build` → output directory `dist`.
3. Set the environment variable:

| Variable | Example | Notes |
|----------|---------|-------|
| `VITE_API_BASE_URL` | `https://your-backend.onrender.com/api` | the deployed backend base URL |

> In development this is `/api` (proxied by Vite). In production it must be the
> **full backend URL** ending in `/api`, because there is no dev proxy.

4. Redeploy. The SPA now calls the deployed backend directly (CORS is allowed
   because `FRONTEND_ORIGIN` on the backend matches the frontend's origin).

## 4. Post-deploy checklist

- [ ] `JWT_SECRET` is a strong, unique value (not the dev default)
- [ ] Demo passwords changed or demo users removed
- [ ] `FRONTEND_ORIGIN` matches the deployed frontend exactly (no trailing slash)
- [ ] `VITE_API_BASE_URL` points at the deployed backend `/api`
- [ ] Swagger `/docs` loads on the backend URL
- [ ] Login works end to end from the deployed frontend
- [ ] No `.env` files committed to Git

## Optional — Docker (local full container)

A backend `Dockerfile` is provided. Build and run:

```bash
cd backend
docker build -t cem-backend .
docker run -p 8000:8000 --env-file .env cem-backend
```

> Docker was not available in the development shell, so the Dockerfile is
> hand-verified, not built here.

## Switching the local database to PostgreSQL

No code changes — only configuration:

```bash
pip install psycopg2-binary
# in backend/.env:
DATABASE_URL=postgresql+psycopg2://cem_user:cem_pass@localhost:5432/circular
python seed.py
```

The SQLAlchemy models are database-agnostic; the same schema is created on both
SQLite and PostgreSQL.
