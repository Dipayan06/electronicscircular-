"""Rule-Based Circularity Recommendation Engine (FR-D) — the AUTHORITATIVE version.

IMPORTANT: this is NOT artificial intelligence. It is a transparent, fully
deterministic set of rules over the assessment inputs (Phase 0 §6). The frontend
carried a preview copy (Phase 4); this backend service is now the single source
of truth. Given identical inputs it always returns the identical output — which
makes it unit-testable (see tests/test_recommendation.py).

Circularity priority ladder (Phase 0 §1): 1 Repair · 2 Reuse · 3 Resale ·
4 Refurbish · 5 Recycle — always prefer the option that retains the most value.
"""

PRIORITY = {"REPAIR": 1, "REUSE": 2, "RESALE": 3, "REFURBISH": 4, "RECYCLE": 5}

NEXT_STEP = {
    "REPAIR": "Find verified repair providers and request a quotation.",
    "REUSE": "Keep using it, or hand it to a new user in good conscience.",
    "RESALE": "List the device on the marketplace to transfer its value.",
    "REFURBISH": "Send it to a verified refurbisher to restore sellable condition.",
    "RECYCLE": "Request a collection so the materials are recovered responsibly.",
}


def _result(action: str, reason: str) -> dict:
    return {"action": action, "priority": PRIORITY[action], "reason": reason, "nextStep": NEXT_STEP[action]}


def recommend(a: dict) -> dict:
    """Evaluate an assessment dict and return the recommended circular action.

    Expected keys: screen ('good'|'minor'|'cracked'), battery ('good'|'weak'|
    'dead'), body ('good'|'scratched'|'damaged'), powers_on/charging/water_damage
    (bool), age_years (int).
    """
    severe = [label for cond, label in (
        (a.get("screen") == "cracked", "cracked screen"),
        (a.get("battery") == "dead", "dead battery"),
        (a.get("body") == "damaged", "damaged body"),
    ) if cond]

    minor = [label for cond, label in (
        (a.get("screen") == "minor", "minor screen wear"),
        (a.get("battery") == "weak", "weak battery"),
        (a.get("body") == "scratched", "body scratches"),
    ) if cond]

    powers_on = bool(a.get("powers_on"))
    charges = bool(a.get("charging"))
    water = bool(a.get("water_damage"))
    old = int(a.get("age_years") or 0) >= 6
    issues = len(severe)

    # Rule 1 — not economically repairable → RECYCLE (priority 5).
    if not powers_on and (water or issues >= 2 or old):
        why = ", ".join(w for w in (
            "water damage" if water else None,
            "high age" if old else None,
            "multiple major faults" if issues >= 2 else None,
        ) if w)
        return _result("RECYCLE",
                       f"The device does not power on and is not economically repairable ({why}). "
                       "Recovering its materials is the best remaining option.")

    # Rule 2 — significant but repairable damage → REFURBISH (priority 4).
    if issues >= 2 or (water and powers_on):
        detail = ", ".join(severe) if severe else "water exposure"
        return _result("REFURBISH",
                       f"The device has significant but repairable damage ({detail}). "
                       "Professional refurbishment can restore it to sellable condition.")

    # Rule 3 — a fault or one major issue that is repairable → REPAIR (priority 1).
    if not powers_on or not charges or issues == 1:
        fault = ("it does not power on" if not powers_on
                 else "it does not charge" if not charges
                 else f"a {severe[0]}")
        return _result("REPAIR",
                       f"The device is largely intact but has a fault ({fault}) that appears repairable.")

    # Rule 4 — fully functional, older or with minor wear → RESALE (priority 3).
    if old or len(minor) >= 1:
        extra = f" with only {' and '.join(minor)}" if minor else ""
        return _result("RESALE",
                       f"The device is fully functional{extra}. "
                       "Selling it transfers its remaining value to a new owner.")

    # Rule 5 — fully functional, excellent condition → REUSE (priority 2).
    return _result("REUSE",
                   "The device is fully functional and in excellent condition — "
                   "it can be reused directly with no intervention.")
