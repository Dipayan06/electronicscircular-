# Circular Electronics Marketplace — Backend

FastAPI + SQLAlchemy backend. **Phase 5** delivers the database layer:
configuration, connection, SQLAlchemy models for all 18 tables, and a seed
script. The FastAPI application, routers and schemas arrive in Phase 6+.

## Tech stack
- FastAPI + Uvicorn (from Phase 6)
- SQLAlchemy 2.0 (ORM / data-access layer)
- Pydantic + pydantic-settings (validation / config)
- PostgreSQL, with a zero-setup SQLite fallback for local development
- passlib + bcrypt (password hashing)

## Setup
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env      # macOS/Linux: cp .env.example .env
```

## Create + seed the database
```bash
python seed.py
```
This drops/creates all tables and inserts demo data. With the default
`DATABASE_URL` it writes a local `circular.db` SQLite file — no database server
needed.

Demo accounts (development passwords — change for any real deployment):
| Role     | Email                     | Password    |
|----------|---------------------------|-------------|
| Consumer | demo.user@example.com     | password123 |
| Provider | demo.provider@example.com | password123 |
| Admin    | admin@example.com         | password123 |

## Using PostgreSQL instead
1. `pip install psycopg2-binary` (or uncomment it in requirements.txt)
2. In `.env`, set `DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/circular`
3. `python seed.py`

The SQLAlchemy models are identical for both databases — only the URL changes.

## Structure
```
backend/
├── app/
│   ├── config.py            settings from .env (pydantic-settings)
│   ├── database.py          engine, SessionLocal, Base, get_db
│   ├── models/              SQLAlchemy models (18 tables) + enums
│   └── utils/security.py    password hashing (bcrypt)
├── seed.py                  create tables + demo data
├── requirements.txt
└── .env.example
```
