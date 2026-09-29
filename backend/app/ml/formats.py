"""Prompt / answer formats shared by the training data generator and the API.

Keeping these in one place guarantees the model sees exactly the same field
layout at inference time as it did during training.
"""
FIELDS = ("screen", "battery", "body", "power", "charging", "water")
ALLOWED = {
    "screen": ("good", "minor", "cracked"),
    "battery": ("good", "weak", "dead"),
    "body": ("good", "scratched", "damaged"),
    "power": ("yes", "no"),
    "charging": ("yes", "no"),
    "water": ("yes", "no"),
}
DEVICE_TYPES = ("smartphone", "laptop", "tablet")


def _yn(v) -> str:
    return "yes" if v else "no"


def encode_assessment(a: dict) -> str:
    """{'screen': 'cracked', 'powers_on': True, ...} -> 'screen=cracked;...;water=no'"""
    return ";".join([
        f"screen={a['screen']}", f"battery={a['battery']}", f"body={a['body']}",
        f"power={_yn(a['powers_on'])}", f"charging={_yn(a['charging'])}", f"water={_yn(a['water_damage'])}",
    ])


def decode_assessment(text: str) -> dict | None:
    """Strictly parse the model's structured answer. Anything malformed → None."""
    parts = dict(p.split("=", 1) for p in text.strip().split(";") if "=" in p)
    if set(parts) != set(FIELDS) or any(parts[f] not in ALLOWED[f] for f in FIELDS):
        return None
    return {
        "screen": parts["screen"], "battery": parts["battery"], "body": parts["body"],
        "powers_on": parts["power"] == "yes", "charging": parts["charging"] == "yes",
        "water_damage": parts["water"] == "yes",
    }


def explain_prompt(action: str, device_type: str, age_years: int, a: dict) -> str:
    return f"rec={action};type={device_type};age={min(max(int(age_years), 0), 15)};" + encode_assessment(a)


def listing_prompt(device_type: str, age_years: int | None, a: dict | None) -> str:
    age = "na" if age_years is None else str(min(max(int(age_years), 0), 15))
    return f"type={device_type};age={age};" + (encode_assessment(a) if a else "assessed=no")
