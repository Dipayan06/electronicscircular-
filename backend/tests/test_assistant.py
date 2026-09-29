"""Circular assistant (in-house small language model) tests.

Covers the NumPy runtime, the strict output validation, the four endpoints,
ownership rules, and, most importantly, that the assistant can never
contradict the rule engine or leave the user without an answer when the model
is unavailable.
"""
import pytest

from app.ml import slm
from app.ml.formats import ALLOWED, decode_assessment
from app.services import assistant_service
from tests.conftest import auth_header, register, token_for

SCREEN, BATTERY, BODY = ALLOWED["screen"], ALLOWED["battery"], ALLOWED["body"]

DEAD_TABLET = {"screen": "cracked", "battery": "dead", "body": "damaged",
               "powers_on": False, "charging": False, "water_damage": True}
CRACKED_ONLY = {"screen": "cracked", "battery": "good", "body": "good",
                "powers_on": True, "charging": True, "water_damage": False}

needs_model = pytest.mark.skipif(slm.get_model() is None, reason="trained weights not present")


def _user(client, email):
    register(client, email)
    return auth_header(token_for(client, email))


def _device(client, h, **kw):
    body = {"type": "laptop", "brand": "Dell", "model": "XPS 13", "purchase_year": 2021, **kw}
    return client.post("/api/devices", headers=h, json=body).json()["data"]["id"]


# ---------------- model runtime ----------------

@needs_model
def test_model_loads_and_is_small():
    m = slm.get_model()
    assert m.n_params < 5_000_000  # a genuinely small language model
    assert m.tok.vocab_size == m.config["vocab"]


@needs_model
def test_generation_is_deterministic():
    m = slm.get_model()
    a = m.generate("chat", "how do i sell my phone")
    b = m.generate("chat", "how do i sell my phone")
    assert a == b and a["finished"]


def test_decode_assessment_is_strict():
    ok = decode_assessment("screen=cracked;battery=good;body=good;power=no;charging=yes;water=no")
    assert ok == {"screen": "cracked", "battery": "good", "body": "good",
                  "powers_on": False, "charging": True, "water_damage": False}
    assert decode_assessment("screen=cracked;battery=good") is None  # missing fields
    assert decode_assessment("screen=exploded;battery=good;body=good;power=no;charging=yes;water=no") is None
    assert decode_assessment("gibberish") is None


# ---------------- endpoints ----------------

def test_status_is_public(client):
    r = client.get("/api/assistant/status")
    assert r.status_code == 200
    assert "available" in r.json()["data"]


def test_assistant_endpoints_require_login(client):
    assert client.post("/api/assistant/chat", json={"message": "hi"}).status_code == 401
    assert client.post("/api/assistant/parse-assessment", json={"text": "cracked screen"}).status_code == 401
    assert client.post("/api/assistant/explain", json={"device_id": 1}).status_code == 401
    assert client.post("/api/assistant/listing-draft", json={"device_id": 1}).status_code == 401


def test_chat_replies(client):
    h = _user(client, "chat@gmail.com")
    r = client.post("/api/assistant/chat", headers=h, json={"message": "how do i recycle my old phone?"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["reply"] and data["source"] in ("model", "fallback")


def test_chat_rejects_empty_message(client):
    h = _user(client, "empty@gmail.com")
    assert client.post("/api/assistant/chat", headers=h, json={"message": ""}).status_code == 422


def test_parse_returns_valid_assessment(client):
    h = _user(client, "parse@gmail.com")
    r = client.post("/api/assistant/parse-assessment", headers=h,
                    json={"text": "the screen is cracked and it won't turn on"})
    assert r.status_code == 200
    a = r.json()["data"]["assessment"]
    assert a["screen"] in SCREEN and a["battery"] in BATTERY and a["body"] in BODY
    assert a["screen"] == "cracked" and a["powers_on"] is False


def test_explain_needs_an_assessment(client):
    h = _user(client, "explain0@gmail.com")
    dev = _device(client, h)
    assert client.post("/api/assistant/explain", headers=h, json={"device_id": dev}).status_code == 404


@pytest.mark.parametrize("i,assessment", [(1, DEAD_TABLET), (2, CRACKED_ONLY)])
def test_explain_never_contradicts_rule_engine(client, i, assessment):
    h = _user(client, f"explain{i}@gmail.com")
    dev = _device(client, h, type="tablet", purchase_year=2016)
    engine = client.post(f"/api/devices/{dev}/assessment", headers=h, json=assessment).json()["data"]["recommendation"]
    r = client.post("/api/assistant/explain", headers=h, json={"device_id": dev})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["recommendation"]["action"] == engine["action"]
    assert assistant_service.ACTION_WORDS[engine["action"]] in data["explanation"].lower() or data["source"] == "rules"


def test_listing_draft_uses_real_device_name(client):
    h = _user(client, "draft@gmail.com")
    dev = _device(client, h)
    client.post(f"/api/devices/{dev}/assessment", headers=h, json=CRACKED_ONLY)
    r = client.post("/api/assistant/listing-draft", headers=h, json={"device_id": dev})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["title"].startswith("Dell XPS 13")
    assert "Dell XPS 13" in d["description"] and "{" not in d["description"]


def test_listing_draft_without_assessment_or_year(client):
    h = _user(client, "draft2@gmail.com")
    dev = _device(client, h, purchase_year=None)
    r = client.post("/api/assistant/listing-draft", headers=h, json={"device_id": dev})
    assert r.status_code == 200
    assert "{" not in r.json()["data"]["description"]


def test_cannot_use_someone_elses_device(client):
    owner = _user(client, "owner@gmail.com")
    other = _user(client, "other@gmail.com")
    dev = _device(client, owner)
    client.post(f"/api/devices/{dev}/assessment", headers=owner, json=CRACKED_ONLY)
    assert client.post("/api/assistant/explain", headers=other, json={"device_id": dev}).status_code == 404
    assert client.post("/api/assistant/listing-draft", headers=other, json={"device_id": dev}).status_code == 404


# ---------------- graceful fallback without the model ----------------

def test_everything_still_works_without_model(client, monkeypatch):
    monkeypatch.setattr(assistant_service, "get_model", lambda: None)
    h = _user(client, "nomodel@gmail.com")
    assert client.get("/api/assistant/status").json()["data"]["available"] is False

    chat = client.post("/api/assistant/chat", headers=h, json={"message": "hello"}).json()["data"]
    assert chat["source"] == "fallback" and chat["reply"]

    parsed = client.post("/api/assistant/parse-assessment", headers=h,
                         json={"text": "battery drains fast and it got wet"}).json()["data"]
    assert parsed["source"] == "rules"
    assert parsed["assessment"]["battery"] == "weak" and parsed["assessment"]["water_damage"] is True

    dev = _device(client, h)
    client.post(f"/api/devices/{dev}/assessment", headers=h, json=CRACKED_ONLY)
    exp = client.post("/api/assistant/explain", headers=h, json={"device_id": dev}).json()["data"]
    assert exp["source"] == "rules" and exp["recommendation"]["action"] == "REPAIR"
    assert exp["explanation"].startswith(exp["recommendation"]["reason"])

    draft = client.post("/api/assistant/listing-draft", headers=h, json={"device_id": dev}).json()["data"]
    assert draft["source"] == "template" and draft["title"] == "Dell XPS 13"
