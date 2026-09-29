"""Circular assistant — the in-house small language model (app/ml) put to work.

Four features, each with a guard and a deterministic fallback so the user
always gets a sensible answer even if the model is unsure or its weights are
missing:

  chat          help questions about the platform
  parse         free-text fault description -> assessment form values
  explain       friendlier, longer explanation of the rule engine's result
  listing_draft title + description for a marketplace listing

The model never makes decisions. Recommendations still come only from the
rule engine (services/recommendation.py). The model explains them, and the
parsed assessment is a pre-fill the user reviews before submitting.
"""
import re
from datetime import datetime

from sqlalchemy.orm import Session

from ..ml.formats import decode_assessment, explain_prompt, listing_prompt
from ..ml.slm import get_model
from ..models import Device, DeviceAssessment, User
from ..utils.responses import APIError
from .recommendation import recommend

# Below these, the answer is treated as a guess and the fallback is used instead.
CHAT_MIN_CONFIDENCE = 0.80
TEXT_MIN_CONFIDENCE = 0.70

CHAT_FALLBACK = ("Sorry, I'm not sure about that one. I can help with registering and assessing devices, "
                 "repair quotes and bookings, selling or buying on the marketplace, and recycling collections.")

# Words the explanation must contain for the recommended action, so a garbled
# answer can never contradict the rule engine.
ACTION_WORDS = {"REPAIR": "repair", "REUSE": "keep using", "RESALE": "marketplace",
                "REFURBISH": "refurbish", "RECYCLE": "recycl"}


def status() -> dict:
    model = get_model()
    if not model:
        return {"available": False, "parameters": 0}
    return {"available": True, "parameters": int(model.n_params), "layers": model.n_layer,
            "d_model": model.d, "context": model.ctx, "vocab": model.tok.vocab_size}


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

def chat(message: str) -> dict:
    model = get_model()
    text = message.strip().lower()[:300]
    if model:
        out = model.generate("chat", text, max_new_tokens=110)
        if out["finished"] and out["confidence"] >= CHAT_MIN_CONFIDENCE and out["text"]:
            return {"reply": out["text"], "source": "model", "confidence": round(out["confidence"], 3)}
        return {"reply": CHAT_FALLBACK, "source": "fallback", "confidence": round(out["confidence"], 3)}
    return {"reply": CHAT_FALLBACK, "source": "fallback", "confidence": 0.0}


# ---------------------------------------------------------------------------
# Free text -> assessment
# ---------------------------------------------------------------------------

_RULES = [  # (regex, field, value) — used only when the model's answer is unusable
    (r"crack|shatter|smash|broken (screen|display|glass)|(screen|display|lcd|glass) (is )?broken", "screen", "cracked"),
    (r"scratch(es)? on the (screen|display|glass)|(screen|display).{0,20}(scuff|scratch|wear)", "screen", "minor"),
    (r"battery.{0,25}(dead|swollen|no charge|won'?t hold|doesn'?t hold any)", "battery", "dead"),
    (r"battery.{0,25}(drain|weak|poor|low|doesn'?t last|fast)|weak battery", "battery", "weak"),
    (r"(bent|dent|hinge|casing|housing|frame|back (cover|glass)|chassis|lid).{0,20}(broken|damaged|crack|bent|shatter)|badly dented|bent", "body", "damaged"),
    (r"(body|back|case|casing|frame|corners|lid).{0,20}(scratch|scuff)|(scratch|scuff).{0,20}(body|back|case|frame)", "body", "scratched"),
    (r"won'?t (turn on|boot|start|power)|doesn'?t (turn|power) on|not (turn|power)ing on|no signs of life|does not (switch|turn|power) on", "powers_on", False),
    (r"won'?t charge|not charging|doesn'?t charge|charging port|stopped charging", "charging", False),
    (r"water|wet|liquid|spill|soak|pool|toilet|rain", "water_damage", True),
]
_DEFAULT = {"screen": "good", "battery": "good", "body": "good",
            "powers_on": True, "charging": True, "water_damage": False}


def _rule_parse(text: str) -> dict:
    result = dict(_DEFAULT)
    for pattern, field, value in _RULES:
        if result[field] == _DEFAULT[field] and re.search(pattern, text):
            result[field] = value
    if re.search(r"no water|never (been|had).{0,10}(wet|water|liquid)", text):
        result["water_damage"] = False
    return result


def parse_description(text: str) -> dict:
    text = text.strip().lower()[:400]
    model = get_model()
    if model:
        out = model.generate("parse", text, max_new_tokens=40)
        parsed = decode_assessment(out["text"]) if out["finished"] else None
        if parsed:
            return {"assessment": parsed, "source": "model", "confidence": round(out["confidence"], 3)}
    return {"assessment": _rule_parse(text), "source": "rules", "confidence": None}


# ---------------------------------------------------------------------------
# Device helpers
# ---------------------------------------------------------------------------

def _owned_device(db: Session, user: User, device_id: int) -> Device:
    device = db.query(Device).filter(Device.id == device_id, Device.owner_id == user.id).first()
    if not device:
        raise APIError("Device not found", status_code=404)
    return device


def _latest_assessment(db: Session, device: Device) -> dict | None:
    a = (db.query(DeviceAssessment).filter(DeviceAssessment.device_id == device.id)
         .order_by(DeviceAssessment.created_at.desc(), DeviceAssessment.id.desc()).first())
    if not a:
        return None
    return {"screen": a.screen, "battery": a.battery, "body": a.body,
            "powers_on": a.powers_on, "charging": a.charging, "water_damage": a.water_damage}


def _age(device: Device) -> int | None:
    return max(0, datetime.utcnow().year - device.purchase_year) if device.purchase_year else None


# ---------------------------------------------------------------------------
# Explain the recommendation
# ---------------------------------------------------------------------------

def explain(db: Session, user: User, device_id: int) -> dict:
    device = _owned_device(db, user, device_id)
    a = _latest_assessment(db, device)
    if not a:
        raise APIError("This device has not been assessed yet", status_code=404)
    age = _age(device) or 0
    rec = recommend({**a, "age_years": age})

    model = get_model()
    if model:
        out = model.generate("explain", explain_prompt(rec["action"], device.type, age, a), max_new_tokens=150)
        text = out["text"]
        if (out["finished"] and out["confidence"] >= TEXT_MIN_CONFIDENCE
                and ACTION_WORDS[rec["action"]] in text.lower()):
            return {"explanation": text, "source": "model", "confidence": round(out["confidence"], 3),
                    "recommendation": rec}
    return {"explanation": f"{rec['reason']} {rec['nextStep']}", "source": "rules", "confidence": None,
            "recommendation": rec}


# ---------------------------------------------------------------------------
# Listing draft
# ---------------------------------------------------------------------------

def _fill(text: str, name: str, year: int | None) -> str:
    text = text.replace(" from {year}", f" from {year}" if year else "").replace("{year}", str(year or ""))
    return text.replace("{device}", name)


def listing_draft(db: Session, user: User, device_id: int) -> dict:
    device = _owned_device(db, user, device_id)
    a = _latest_assessment(db, device)
    age = _age(device)
    name = f"{device.brand} {device.model}".strip()

    model = get_model()
    if model:
        out = model.generate("listing", listing_prompt(device.type, age, a), max_new_tokens=150)
        if out["finished"] and out["confidence"] >= TEXT_MIN_CONFIDENCE and out["text"].count("|") == 1:
            tagline, body = (s.strip() for s in out["text"].split("|"))
            leftover = re.search(r"\{\w*\}?", _fill(body, name, device.purchase_year))
            if tagline and body and not leftover:
                return {"title": f"{name} - {tagline}"[:160],
                        "description": _fill(body, name, device.purchase_year),
                        "source": "model", "confidence": round(out["confidence"], 3)}

    # Template fallback
    year = f" from {device.purchase_year}" if device.purchase_year else ""
    desc = f"Selling my {name}{year}."
    if a:
        desc += (f" Screen: {a['screen']}. Battery: {a['battery']}. Body: {a['body']}."
                 f" {'Powers on' if a['powers_on'] else 'Does not power on'}."
                 f"{'' if a['charging'] else ' Does not charge.'}{' Has had water exposure.' if a['water_damage'] else ''}")
    return {"title": name[:160], "description": desc, "source": "template", "confidence": None}
