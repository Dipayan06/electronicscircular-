"""Unit tests for the Rule-Based Circularity Recommendation Engine (FR-D).

These prove the engine is deterministic and that each circular action is reachable
with the expected priority — the kind of business-rule test the brief asks for
(§16). Run:  pytest -q
"""
import pytest

from app.services.recommendation import recommend, PRIORITY

# A device in perfect working order.
PRISTINE = dict(screen="good", battery="good", body="good",
                powers_on=True, charging=True, water_damage=False, age_years=1)


def test_pristine_device_is_reused():
    r = recommend(PRISTINE)
    assert r["action"] == "REUSE"
    assert r["priority"] == 2


def test_functional_with_minor_wear_is_resold():
    r = recommend({**PRISTINE, "battery": "weak"})
    assert r["action"] == "RESALE"
    assert r["priority"] == 3


def test_functional_but_old_is_resold():
    r = recommend({**PRISTINE, "age_years": 8})
    assert r["action"] == "RESALE"


def test_single_major_fault_is_repaired():
    r = recommend({**PRISTINE, "screen": "cracked"})
    assert r["action"] == "REPAIR"
    assert r["priority"] == 1


def test_not_charging_is_repaired():
    r = recommend({**PRISTINE, "charging": False})
    assert r["action"] == "REPAIR"


def test_two_major_faults_is_refurbished():
    r = recommend({**PRISTINE, "screen": "cracked", "battery": "dead"})
    assert r["action"] == "REFURBISH"
    assert r["priority"] == 4


def test_dead_and_water_damaged_is_recycled():
    r = recommend({**PRISTINE, "powers_on": False, "water_damage": True})
    assert r["action"] == "RECYCLE"
    assert r["priority"] == 5


def test_dead_and_old_is_recycled():
    r = recommend({**PRISTINE, "powers_on": False, "age_years": 9, "battery": "dead"})
    assert r["action"] == "RECYCLE"


def test_engine_is_deterministic():
    """Same input → identical output, every time (core FR-D property)."""
    sample = {**PRISTINE, "screen": "cracked"}
    first = recommend(sample)
    for _ in range(50):
        assert recommend(sample) == first


def test_reason_and_next_step_present():
    r = recommend(PRISTINE)
    assert r["reason"] and r["nextStep"]
    assert r["priority"] == PRIORITY[r["action"]]


@pytest.mark.parametrize("action", ["REPAIR", "REUSE", "RESALE", "REFURBISH", "RECYCLE"])
def test_all_actions_are_reachable(action):
    cases = {
        "REPAIR": {**PRISTINE, "screen": "cracked"},
        "REUSE": PRISTINE,
        "RESALE": {**PRISTINE, "battery": "weak"},
        "REFURBISH": {**PRISTINE, "screen": "cracked", "body": "damaged"},
        "RECYCLE": {**PRISTINE, "powers_on": False, "water_damage": True},
    }
    assert recommend(cases[action])["action"] == action
