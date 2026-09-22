"""API + integration tests (Phase 16, brief §39).

Exercises the real endpoints through FastAPI's TestClient against an isolated
database. Covers authentication, device CRUD, ownership isolation, the
assessment/recommendation endpoint, and two complete end-to-end workflows
(repair journey and recycle journey).
"""
from tests.conftest import register, token_for, auth_header, PROVIDER_EMAIL, TEST_PASSWORD


# ---------------- System ----------------

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["success"] is True


# ---------------- Authentication (AUTH-01..) ----------------

def test_register_returns_token_and_user(client):
    r = register(client, "alice@test.com")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["token"]
    assert data["user"]["email"] == "alice@test.com"
    assert data["user"]["role"] == "consumer"


def test_duplicate_email_rejected(client):
    register(client, "bob@test.com")
    r = register(client, "bob@test.com")
    assert r.status_code == 409
    assert r.json()["success"] is False


def test_login_success_and_failure(client):
    register(client, "carol@test.com")
    ok = client.post("/api/auth/login", json={"email": "carol@test.com", "password": TEST_PASSWORD})
    assert ok.status_code == 200
    bad = client.post("/api/auth/login", json={"email": "carol@test.com", "password": "wrong"})
    assert bad.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401
    register(client, "dave@test.com")
    token = token_for(client, "dave@test.com")
    r = client.get("/api/auth/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["data"]["email"] == "dave@test.com"


def test_password_is_hashed_not_returned(client):
    r = register(client, "erin@test.com")
    assert "password" not in r.json()["data"]["user"]
    assert "password_hash" not in r.json()["data"]["user"]


# ---------------- Device CRUD (DEV-01..) ----------------

def _consumer(client, email="user1@test.com"):
    register(client, email)
    return token_for(client, email)


def test_device_crud(client):
    h = auth_header(_consumer(client))
    # create
    r = client.post("/api/devices", headers=h,
                    json={"type": "laptop", "brand": "Dell", "model": "XPS 13", "purchase_year": 2021})
    assert r.status_code == 201
    dev_id = r.json()["data"]["id"]
    # list
    assert len(client.get("/api/devices", headers=h).json()["data"]) == 1
    # get
    assert client.get(f"/api/devices/{dev_id}", headers=h).json()["data"]["brand"] == "Dell"
    # update
    up = client.put(f"/api/devices/{dev_id}", headers=h, json={"working_status": "faulty"})
    assert up.json()["data"]["working_status"] == "faulty"
    # delete
    assert client.delete(f"/api/devices/{dev_id}", headers=h).status_code == 200
    assert len(client.get("/api/devices", headers=h).json()["data"]) == 0


def test_device_requires_auth(client):
    assert client.get("/api/devices").status_code == 401


def test_invalid_device_type_rejected(client):
    h = auth_header(_consumer(client))
    r = client.post("/api/devices", headers=h, json={"type": "fridge", "brand": "X", "model": "Y"})
    assert r.status_code == 422


def test_device_ownership_isolation(client):
    # user A creates a device
    ha = auth_header(_consumer(client, "owner@test.com"))
    dev_id = client.post("/api/devices", headers=ha,
                         json={"type": "tablet", "brand": "Samsung", "model": "Tab"}).json()["data"]["id"]
    # user B cannot see it
    hb = auth_header(_consumer(client, "intruder@test.com"))
    assert client.get(f"/api/devices/{dev_id}", headers=hb).status_code == 404
    assert len(client.get("/api/devices", headers=hb).json()["data"]) == 0


# ---------------- Assessment + recommendation (ASS/REC) ----------------

def test_assessment_returns_recycle_for_dead_device(client):
    h = auth_header(_consumer(client))
    dev_id = client.post("/api/devices", headers=h,
                         json={"type": "tablet", "brand": "Old", "model": "Tab", "purchase_year": 2016}).json()["data"]["id"]
    r = client.post(f"/api/devices/{dev_id}/assessment", headers=h, json={
        "screen": "cracked", "battery": "dead", "body": "damaged",
        "powers_on": False, "charging": False, "water_damage": True,
    })
    assert r.status_code == 200
    rec = r.json()["data"]["recommendation"]
    assert rec["action"] == "RECYCLE"
    assert rec["priority"] == 5
    # recommendation is retrievable afterwards
    got = client.get(f"/api/devices/{dev_id}/recommendation", headers=h)
    assert got.json()["data"]["recommendation"]["action"] == "RECYCLE"


def test_recommendation_404_before_assessment(client):
    h = auth_header(_consumer(client))
    dev_id = client.post("/api/devices", headers=h,
                         json={"type": "laptop", "brand": "New", "model": "Book"}).json()["data"]["id"]
    assert client.get(f"/api/devices/{dev_id}/recommendation", headers=h).status_code == 404


# ---------------- RBAC ----------------

def test_non_admin_cannot_verify_provider(client):
    h = auth_header(_consumer(client))
    pid = client.get("/api/providers").json()["data"][0]["id"]
    assert client.put(f"/api/providers/{pid}/verify", headers=h).status_code == 403


def test_admin_role_cannot_be_self_registered(client):
    # admin accounts are created via the seed only, not public signup
    r = register(client, "admin2@test.com", role="admin")
    assert r.status_code == 422


# ---------------- End-to-end: repair journey (integration) ----------------

def test_full_repair_workflow(client):
    hc = auth_header(_consumer(client, "repair@test.com"))
    hp = auth_header(token_for(client, PROVIDER_EMAIL))

    dev_id = client.post("/api/devices", headers=hc,
                         json={"type": "laptop", "brand": "Dell", "model": "XPS", "purchase_year": 2021}).json()["data"]["id"]
    pid = client.get("/api/providers").json()["data"][0]["id"]

    # request → quote → accept → book → complete
    q = client.post("/api/quotations", headers=hc,
                    json={"device_id": dev_id, "provider_id": pid, "problem": "cracked screen"}).json()["data"]
    assert q["status"] == "PENDING"
    client.put(f"/api/quotations/{q['id']}/quote", headers=hp,
               json={"cost": 4200, "days": 3, "description": "screen"})
    accepted = client.put(f"/api/quotations/{q['id']}/accept", headers=hc).json()["data"]
    assert accepted["status"] == "ACCEPTED"
    booking = client.post("/api/bookings", headers=hc, json={"quotation_id": q["id"]}).json()["data"]
    assert booking["status"] == "CONFIRMED"
    client.put(f"/api/bookings/{booking['id']}/status", headers=hp, json={"status": "IN_PROGRESS"})
    done = client.put(f"/api/bookings/{booking['id']}/status", headers=hp, json={"status": "COMPLETED"}).json()["data"]
    assert done["status"] == "COMPLETED"

    # lifecycle reflects the whole journey
    types = [e["type"] for e in client.get(f"/api/devices/{dev_id}/lifecycle", headers=hc).json()["data"]]
    for expected in ["DEVICE_REGISTERED", "QUOTE_REQUESTED", "QUOTE_ACCEPTED", "BOOKING_CONFIRMED", "REPAIR_COMPLETED"]:
        assert expected in types


def test_cannot_book_unaccepted_quote(client):
    hc = auth_header(_consumer(client, "nobook@test.com"))
    dev_id = client.post("/api/devices", headers=hc,
                         json={"type": "laptop", "brand": "Dell", "model": "XPS"}).json()["data"]["id"]
    pid = client.get("/api/providers").json()["data"][0]["id"]
    q = client.post("/api/quotations", headers=hc,
                    json={"device_id": dev_id, "provider_id": pid, "problem": "broken hinge"}).json()["data"]
    # try to book a PENDING quote
    r = client.post("/api/bookings", headers=hc, json={"quotation_id": q["id"]})
    assert r.status_code == 400


# ---------------- End-to-end: recycle journey (integration) ----------------

def test_full_recycle_workflow(client):
    hc = auth_header(_consumer(client, "recycle@test.com"))
    dev_id = client.post("/api/devices", headers=hc,
                         json={"type": "tablet", "brand": "Old", "model": "Tab", "purchase_year": 2015}).json()["data"]["id"]
    pid = client.get("/api/providers").json()["data"][0]["id"]

    c = client.post("/api/collections", headers=hc,
                    json={"device_id": dev_id, "collector_id": pid, "address": "MG Road"}).json()["data"]
    assert c["status"] == "REQUESTED"
    for s in ["SCHEDULED", "PICKED_UP", "RECEIVED", "RECYCLED"]:
        client.put(f"/api/collections/{c['id']}/status", headers=hc, json={"status": s})
    # backward move rejected
    bad = client.put(f"/api/collections/{c['id']}/status", headers=hc, json={"status": "PICKED_UP"})
    assert bad.status_code == 400

    types = [e["type"] for e in client.get(f"/api/devices/{dev_id}/lifecycle", headers=hc).json()["data"]]
    assert "COLLECTION_REQUESTED" in types and "RECYCLED" in types


# ---------------- Marketplace ----------------

def test_listing_create_and_reserve(client):
    hc = auth_header(_consumer(client, "seller@test.com"))
    listing = client.post("/api/listings", headers=hc, json={
        "title": "iPhone 12", "type": "smartphone", "price": 22000, "condition": "Good",
    }).json()["data"]
    assert listing["status"] == "ACTIVE"
    reserved = client.put(f"/api/listings/{listing['id']}/reserve", headers=hc).json()["data"]
    assert reserved["status"] == "RESERVED"
    # cannot reserve again
    assert client.put(f"/api/listings/{listing['id']}/reserve", headers=hc).status_code == 400
