"""Pytest fixtures (Phase 16).

Provides a FastAPI TestClient wired to an isolated in-memory SQLite database, so
API tests never touch the real circular.db. The `get_db` dependency is overridden
per test; roles and one verified provider (with a login) are seeded so the quote
workflow can be exercised.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401 — register all tables
from datetime import datetime
from decimal import Decimal

from app.models import Role, User, Provider, MaterialPrice
from app.models.enums import ROLES
from app.utils.security import hash_password

PROVIDER_EMAIL = "fixit@gmail.com"
ADMIN_EMAIL = "admin@gmail.com"
TEST_PASSWORD = "testpass1"


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection across the app's sessions
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    # Seed roles + one verified provider that also has a login account.
    db = TestingSession()
    roles = {name: Role(name=name) for name in ROLES}
    db.add_all(roles.values())
    db.flush()
    prov_user = User(name="FixIt Labs", email=PROVIDER_EMAIL,
                     password_hash=hash_password(TEST_PASSWORD), role_id=roles["provider"].id)
    db.add(prov_user)
    db.flush()
    db.add(Provider(user_id=prov_user.id, name="FixIt Labs", type="technician",
                    verified=True, rating=4.6, location="Bengaluru"))
    db.add(User(name="Admin", email=ADMIN_EMAIL, is_verified=True,
                password_hash=hash_password(TEST_PASSWORD), role_id=roles["admin"].id))
    # Reference prices for pricing / regulation tests (band 0.5x-1.5x, extreme 3x).
    for material, price, unit in (("copper", "750", "kg"), ("gold", "6500", "g")):
        db.add(MaterialPrice(material=material, display_name=material.title(), reference_price=Decimal(price),
                             unit=unit, source="Admin reference - test", source_type="admin",
                             observed_at=datetime.utcnow()))
    db.commit()
    db.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---- helpers shared by tests ----

def register(client, email, role="consumer", name="Test User", password=TEST_PASSWORD):
    return client.post("/api/auth/register",
                       json={"name": name, "email": email, "password": password, "role": role})


def token_for(client, email, password=TEST_PASSWORD):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    return r.json()["data"]["token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def verify(client, headers):
    """Complete email verification via the dev-mode self-fetch endpoint."""
    code = client.get("/api/auth/dev/verification-code", headers=headers).json()["data"]["code"]
    r = client.post("/api/auth/verify-email", headers=headers, json={"code": code})
    assert r.status_code == 200, r.text
    return headers
