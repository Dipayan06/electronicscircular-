"""Database connection (Phase 1 §1.2 data layer).

Creates the SQLAlchemy engine + session factory and the declarative Base that all
models inherit from. `get_db` is the FastAPI dependency that yields a session per
request and always closes it (used from Phase 6).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

# SQLite needs check_same_thread=False to be used across FastAPI's threads.
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a database session and guarantee it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
