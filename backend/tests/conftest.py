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
from app.models import Role, User, Provider
from app.models.enums import ROLES
from app.utils.security import hash_password

PROVIDER_EMAIL = "fixit@test.com"
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
