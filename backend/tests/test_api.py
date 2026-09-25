"""API + integration tests (Phase 16, brief §39).

Exercises the real endpoints through FastAPI's TestClient against an isolated
database. Covers authentication, device CRUD, ownership isolation, the
assessment/recommendation endpoint, and two complete end-to-end workflows
(repair journey and recycle journey).
"""
from tests.conftest import register, token_for, auth_header, verify, PROVIDER_EMAIL, ADMIN_EMAIL, TEST_PASSWORD


# ---------------- System ----------------

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["success"] is True


# ---------------- Authentication (AUTH-01..) ----------------

def test_register_returns_token_and_user(client):
    r = register(client, "alice@gmail.com")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["token"]
    assert data["user"]["email"] == "alice@gmail.com"
    assert data["user"]["role"] == "consumer"


def test_duplicate_email_rejected(client):
    register(client, "bob@gmail.com")
    r = register(client, "bob@gmail.com")
    assert r.status_code == 409
    assert r.json()["success"] is False


def test_login_success_and_failure(client):
    register(client, "carol@gmail.com")
    ok = client.post("/api/auth/login", json={"email": "carol@gmail.com", "password": TEST_PASSWORD})
    assert ok.status_code == 200
    bad = client.post("/api/auth/login", json={"email": "carol@gmail.com", "password": "wrong"})
    assert bad.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401
    register(client, "dave@gmail.com")
    token = token_for(client, "dave@gmail.com")
    r = client.get("/api/auth/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["data"]["email"] == "dave@gmail.com"


def test_password_is_hashed_not_returned(client):
    r = register(client, "erin@gmail.com")
    assert "password" not in r.json()["data"]["user"]
    assert "password_hash" not in r.json()["data"]["user"]


# ---------------- Device CRUD (DEV-01..) ----------------

def _consumer(client, email="user1@gmail.com"):
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
    ha = auth_header(_consumer(client, "owner@gmail.com"))
    dev_id = client.post("/api/devices", headers=ha,
                         json={"type": "tablet", "brand": "Samsung", "model": "Tab"}).json()["data"]["id"]
    # user B cannot see it
    hb = auth_header(_consumer(client, "intruder@gmail.com"))
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
    r = register(client, "admin2@gmail.com", role="admin")
    assert r.status_code == 422


# ---------------- End-to-end: repair journey (integration) ----------------

def test_full_repair_workflow(client):
    hc = auth_header(_consumer(client, "repair@gmail.com"))
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
    hc = auth_header(_consumer(client, "nobook@gmail.com"))
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
    hc = auth_header(_consumer(client, "recycle@gmail.com"))
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
    hc = verify(client, auth_header(_consumer(client, "seller@gmail.com")))
    listing = client.post("/api/listings", headers=hc, json={
        "title": "iPhone 12", "type": "smartphone", "price": 22000, "condition": "Good",
    }).json()["data"]
    assert listing["status"] == "ACTIVE"
    reserved = client.put(f"/api/listings/{listing['id']}/reserve", headers=hc).json()["data"]
    assert reserved["status"] == "RESERVED"
    # cannot reserve again
    assert client.put(f"/api/listings/{listing['id']}/reserve", headers=hc).status_code == 400


# ---------------- Feature 1: email verification ----------------

def test_register_rejects_non_allowed_domains(client):
    for email in ["a@hotmail.com", "b@outlook.com", "c@protonmail.com", "d@gmail.co",
                  "e@yahoo.co.in", "f@company.com", "g@mail.gmail.com"]:
        assert register(client, email).status_code == 422, email
    assert register(client, "ok@yahoo.com").status_code == 200


def test_new_user_unverified_cannot_list(client):
    hc = auth_header(_consumer(client, "fresh@gmail.com"))
    assert client.get("/api/auth/me", headers=hc).json()["data"]["is_verified"] is False
    r = client.post("/api/listings", headers=hc, json={"title": "Phone", "type": "smartphone", "price": 100})
    assert r.status_code == 403


def test_wrong_code_rejected_then_verify(client):
    hc = auth_header(_consumer(client, "otp@gmail.com"))
    code = client.get("/api/auth/dev/verification-code", headers=hc).json()["data"]["code"]
    wrong = "000000" if code != "000000" else "111111"
    assert client.post("/api/auth/verify-email", headers=hc, json={"code": wrong}).status_code == 400
    verify(client, hc)
    assert client.get("/api/auth/me", headers=hc).json()["data"]["is_verified"] is True


# ---------------- Feature 3: notifications ----------------

def test_notifications_event_driven_and_user_scoped(client):
    seller = verify(client, auth_header(_consumer(client, "nseller@gmail.com")))
    buyer = verify(client, auth_header(_consumer(client, "nbuyer@gmail.com")))
    listing = client.post("/api/listings", headers=seller, json={
        "title": "Pixel 6", "type": "smartphone", "price": 15000}).json()["data"]
    client.put(f"/api/listings/{listing['id']}/reserve", headers=buyer)

    feed = client.get("/api/notifications", headers=seller).json()["data"]
    order = [n for n in feed["items"] if n["title"] == "New order received"]
    assert order and not order[0]["read"]
    unread_before = feed["unread"]

    # buyer cannot mark the seller's notification (IDOR)
    assert client.put(f"/api/notifications/{order[0]['id']}/read", headers=buyer).status_code == 404
    r = client.put(f"/api/notifications/{order[0]['id']}/read", headers=seller).json()["data"]
    assert r["read"] and r["read_at"]
    after = client.get("/api/notifications/unread-count", headers=seller).json()["data"]["unread"]
    assert after == unread_before - 1

    client.put("/api/notifications/read-all", headers=seller)
    assert client.get("/api/notifications/unread-count", headers=seller).json()["data"]["unread"] == 0
    assert client.get("/api/notifications/unread-count", headers=buyer).json()["data"]["unread"] >= 1


# ---------------- Feature 2: reference pricing ----------------

def test_prices_labelled_reference_not_live(client):
    items = client.get("/api/pricing/materials").json()["data"]["items"]
    copper = [p for p in items if p["material"] == "copper"][0]
    assert copper["status"] == "reference" and copper["is_live"] is False
    assert copper["source"] and copper["observed_at"] and copper["currency"] == "INR"


def test_only_admin_can_set_reference(client):
    hc = auth_header(_consumer(client, "pricehacker@gmail.com"))
    assert client.put("/api/pricing/materials/copper", headers=hc, json={"reference_price": 1}).status_code == 403
    ha = auth_header(token_for(client, ADMIN_EMAIL))
    r = client.put("/api/pricing/materials/copper", headers=ha,
                   json={"reference_price": 800, "source_note": "LME check 25 Sep"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["reference_price"] == 800 and d["source_type"] == "admin" and d["status"] == "reference"
    assert "LME check" in d["source"]
    hist = client.get("/api/pricing/materials/copper/history").json()["data"]
    assert hist[0]["reference_price"] == 800
    # public list reflects the write immediately (cache invalidated)
    items = client.get("/api/pricing/materials").json()["data"]["items"]
    assert [p for p in items if p["material"] == "copper"][0]["reference_price"] == 800


def test_invalid_reference_values_rejected(client):
    ha = auth_header(token_for(client, ADMIN_EMAIL))
    assert client.put("/api/pricing/materials/copper", headers=ha, json={"reference_price": -5}).status_code == 422
    assert client.put("/api/pricing/materials/copper", headers=ha,
                      json={"band_min": 1.2, "band_max": 1.1}).status_code == 422
    assert client.post("/api/pricing/refresh", headers=ha).status_code == 400  # no feed configured


# ---------------- Feature 4: price regulation ----------------

def _material(price, unit="kg", type_="copper", justification=None):
    body = {"kind": "material", "type": type_, "title": "Copper lot", "price": price,
            "unit": unit, "quantity": 10}
    if justification:
        body["price_justification"] = justification
    return body


def test_price_levels_normal_review_extreme(client):
    hs = verify(client, auth_header(_consumer(client, "reg@gmail.com")))
    ok = client.post("/api/listings", headers=hs, json=_material(700)).json()["data"]
    assert ok["status"] == "ACTIVE" and ok["price_assessment"]["level"] == "NORMAL"

    # REVIEW needs a justification
    assert client.post("/api/listings", headers=hs, json=_material(1500)).status_code == 422
    rv = client.post("/api/listings", headers=hs,
                     json=_material(1500, justification="Audio-grade oxygen-free copper")).json()["data"]
    assert rv["status"] == "PRICE_REVIEW_REQUIRED"

    ex = client.post("/api/listings", headers=hs, json=_material(5000)).json()["data"]
    assert ex["status"] == "SUSPENDED_PENDING_REVIEW"

    # unit conversion: 0.7 per g == 700 per kg -> NORMAL
    g = client.post("/api/listings", headers=hs, json=_material(0.7, unit="g")).json()["data"]
    assert g["status"] == "ACTIVE"
    # a unit switch can't bypass regulation
    pc = client.post("/api/listings", headers=hs,
                     json=_material(9999, unit="piece", justification="sold per spool")).json()["data"]
    assert pc["status"] == "PRICE_REVIEW_REQUIRED"

    public = {l["id"] for l in client.get("/api/listings").json()["data"]}
    assert ok["id"] in public and rv["id"] in public and ex["id"] not in public
    # hidden listing: 404 to strangers, visible to its seller
    assert client.get(f"/api/listings/{ex['id']}").status_code == 404
    assert client.get(f"/api/listings/{ex['id']}", headers=hs).status_code == 200
    mine = {l["id"] for l in client.get("/api/listings/mine", headers=hs).json()["data"]}
    assert ex["id"] in mine

    buyer = verify(client, auth_header(_consumer(client, "regbuyer@gmail.com")))
    assert client.put(f"/api/listings/{rv['id']}/reserve", headers=buyer, json={"quantity": 1}).status_code == 400


def test_non_finite_price_rejected(client):
    hs = verify(client, auth_header(_consumer(client, "nan@gmail.com")))
    raw = '{"kind":"material","type":"copper","title":"x lot","price":NaN,"unit":"kg","quantity":1}'
    r = client.post("/api/listings", headers={**hs, "Content-Type": "application/json"}, content=raw)
    assert r.status_code == 422
    assert client.post("/api/listings", headers=hs, json=_material(0)).status_code == 422


def test_admin_review_workflow(client):
    hs = verify(client, auth_header(_consumer(client, "revseller@gmail.com")))
    ex = client.post("/api/listings", headers=hs, json=_material(5000)).json()["data"]
    ha = auth_header(token_for(client, ADMIN_EMAIL))

    # seller can't list all reviews or decide
    assert client.get("/api/price-reviews", headers=hs).status_code == 403
    pending = client.get("/api/price-reviews?status=PENDING", headers=ha).json()["data"]
    review = [r for r in pending if r["listing_id"] == ex["id"]][0]
    assert review["level"] == "EXTREME" and review["reference_price"] == 750
    assert client.put(f"/api/price-reviews/{review['id']}/approve", headers=hs).status_code == 403

    # admin got notified
    admin_feed = client.get("/api/notifications", headers=ha).json()["data"]["items"]
    assert any(n["type"] == "price" for n in admin_feed)

    r = client.put(f"/api/price-reviews/{review['id']}/approve", headers=ha, json={"note": "Verified invoice"})
    assert r.json()["data"]["status"] == "APPROVED" and r.json()["data"]["reviewer"] == "Admin"
    assert client.get(f"/api/listings/{ex['id']}").json()["data"]["status"] == "ACTIVE"
    # decisions are final (audit integrity)
    assert client.put(f"/api/price-reviews/{review['id']}/reject", headers=ha).status_code == 409
    mine = client.get("/api/price-reviews/mine", headers=hs).json()["data"]
    assert mine[0]["reviewer_note"] == "Verified invoice"
    seller_feed = client.get("/api/notifications", headers=hs).json()["data"]["items"]
    assert any(n["title"] == "Price approved" for n in seller_feed)

    # reject path
    ex2 = client.post("/api/listings", headers=hs, json=_material(9000)).json()["data"]
    rid = [r for r in client.get("/api/price-reviews?status=PENDING", headers=ha).json()["data"]
           if r["listing_id"] == ex2["id"]][0]["id"]
    client.put(f"/api/price-reviews/{rid}/reject", headers=ha, json={"note": "No evidence"})
    assert client.get(f"/api/listings/{ex2['id']}", headers=hs).json()["data"]["status"] == "REJECTED"
