"""Resale-value estimate for devices and components.

A transparent, deterministic estimate, NOT a market quote. It never invents a
price: the anchor is either

  1. what the seller says they paid (best), or
  2. the admin-managed typical new price for the category (labelled as such),

which is then depreciated by age and adjusted for condition (the device's
latest assessment when there is one, else the listing condition). If there are
at least MIN_COMPARABLES similar listings on the platform, their median is
blended in. With no anchor and too few comparables, the estimate is simply
"not available". Every factor is returned so the UI can explain the number.
"""
from datetime import datetime, timedelta
from statistics import median
from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import CategoryPrice, Device, ResaleListing, User
from ..models.valuation import VALUED_CATEGORIES
from ..utils.responses import APIError

MIN_COMPARABLES = 3
COMPARABLE_WINDOW_DAYS = 180
COMPARABLE_STATUSES = ("ACTIVE", "RESERVED", "SOLD")
ASSUMED_AGE_YEARS = 2   # used (and disclosed) when the age is unknown

# Condition multipliers. Assessment answers are more specific than the free
# "condition" label, so they take precedence when available.
ASSESSMENT_FACTORS = {
    ("screen", "minor"): (0.90, "minor screen wear"),
    ("screen", "cracked"): (0.60, "cracked screen"),
    ("battery", "weak"): (0.90, "weak battery"),
    ("battery", "dead"): (0.75, "dead battery"),
    ("body", "scratched"): (0.92, "scratched body"),
    ("body", "damaged"): (0.75, "damaged body"),
}
CONDITION_FACTORS = {
    "Excellent": 1.00, "Good": 0.85, "Fair": 0.70, "Refurbished": 0.90, "For parts": 0.25,
}
WORKING_STATUS_FACTORS = {"faulty": (0.60, "reported faulty"), "not_working": (0.30, "not working")}


def _round_price(x: float) -> int:
    """Round to a sensible step so the estimate doesn't look falsely precise."""
    step = 10 if x < 1_000 else 50 if x < 10_000 else 100 if x < 100_000 else 1_000
    return int(round(x / step) * step)


def _condition_multiplier(device: Device | None, condition: str | None) -> tuple[float, list[str]]:
    notes: list[str] = []
    assessment = None
    if device is not None:
        assessment = (device.assessments and
                      sorted(device.assessments, key=lambda a: a.created_at)[-1])
    if assessment is not None:
        m = 1.0
        for (field, value), (factor, label) in ASSESSMENT_FACTORS.items():
            if getattr(assessment, field) == value:
                m *= factor
                notes.append(f"{label} (×{factor:g})")
        if not assessment.powers_on:
            m *= 0.30
            notes.append("doesn't power on (×0.3)")
        elif not assessment.charging:
            m *= 0.80
            notes.append("charging issue (×0.8)")
        if assessment.water_damage:
            m *= 0.50
            notes.append("water damage (×0.5)")
        if not notes:
            notes.append("assessment: no issues found (×1)")
        return m, notes

    m = CONDITION_FACTORS.get(condition or "", 0.85)
    notes.append(f"condition “{condition or 'Good'}” (×{m:g})")
    if device is not None and device.working_status in WORKING_STATUS_FACTORS:
        factor, label = WORKING_STATUS_FACTORS[device.working_status]
        m *= factor
        notes.append(f"{label} (×{factor:g})")
    return m, notes


def _comparables(db: Session, kind: str, category: str, brand: str | None, exclude_seller: int) -> dict:
    since = datetime.utcnow() - timedelta(days=COMPARABLE_WINDOW_DAYS)
    rows = (
        db.query(ResaleListing)
        .filter(ResaleListing.kind == kind, ResaleListing.type == category,
                ResaleListing.status.in_(COMPARABLE_STATUSES),
                ResaleListing.created_at >= since,
                ResaleListing.seller_id != exclude_seller)   # don't let a seller anchor on themselves
        .all()
    )
    prices = [r.price for r in rows]
    # Prefer same-brand listings when there are enough of them.
    if brand:
        same_brand = [r.price for r in rows if brand.lower() in (r.title or "").lower()]
        if len(same_brand) >= MIN_COMPARABLES:
            prices, scope = same_brand, f"{brand} listings"
        else:
            scope = "similar listings"
    else:
        scope = "similar listings"
    return {"count": len(prices), "median": _round_price(median(prices)) if prices else None,
            "low": _round_price(min(prices)) if prices else None,
            "high": _round_price(max(prices)) if prices else None, "scope": scope,
            "_prices": prices}


def estimate(db: Session, user: User, kind: str, category: str, *, purchase_price: float | None = None,
             purchase_year: int | None = None, condition: str | None = None, device_id: int | None = None,
             brand: str | None = None) -> dict:
    if kind not in ("device", "component"):
        raise APIError("Estimates are available for devices and components", status_code=422)
    if purchase_price is not None and not (0 < purchase_price <= 1e8):
        raise APIError("Purchase price must be a positive number", status_code=422)

    device = None
    if device_id is not None:
        # Only the owner's own device can be used (no peeking at others' assessments).
        device = db.query(Device).filter(Device.id == device_id, Device.owner_id == user.id).first()
        if not device:
            raise APIError("Device not found", status_code=404)
        category = device.type
        purchase_year = purchase_year or device.purchase_year
        brand = brand or device.brand

    factors: list[str] = []
    current_year = datetime.utcnow().year
    if purchase_year is not None and not (1990 <= purchase_year <= current_year):
        raise APIError(f"Purchase year must be between 1990 and {current_year}", status_code=422)

    # ---- 1. anchor
    anchor, anchor_label, ref = None, None, None
    if purchase_price:
        anchor, anchor_label = float(purchase_price), "the price you paid"
    elif category in VALUED_CATEGORIES:
        ref = db.query(CategoryPrice).filter(CategoryPrice.category == category).first()
        if ref:
            anchor = float(ref.typical_new_price)
            anchor_label = f"typical new price for a {ref.display_name.lower()} (admin reference)"

    formula = None
    age_known = purchase_year is not None
    if anchor is not None:
        factors.append(f"Starting from {anchor_label}: ₹{anchor:,.0f}")
        # ---- 2. age depreciation
        if ref is None:
            ref = db.query(CategoryPrice).filter(CategoryPrice.category == category).first()
        rate = float(ref.annual_depreciation) if ref else 0.20
        floor = float(ref.residual_floor) if ref else 0.10
        age = max(0, current_year - purchase_year) if age_known else ASSUMED_AGE_YEARS
        dep = max(floor, (1 - rate) ** age)
        factors.append(f"{age} year{'s' if age != 1 else ''} old"
                       f"{'' if age_known else ' (assumed — year unknown)'}: "
                       f"keeps {dep:.0%} of value ({rate:.0%}/year)")
        # ---- 3. condition
        cond_m, cond_notes = _condition_multiplier(device, condition)
        factors.extend(cond_notes)
        formula = anchor * dep * cond_m

    # ---- 4. platform comparables
    comps = _comparables(db, kind, category, brand, user.id)
    usable_comps = comps["count"] >= MIN_COMPARABLES

    if formula is None and not usable_comps:
        return {
            "available": False,
            "reason": ("Not enough information for an estimate. Enter what you paid for it"
                       + (", or ask an admin to set a typical price for this category." if category != "other"
                          else ".")),
            "comparables": {k: v for k, v in comps.items() if not k.startswith("_")},
        }

    if formula is not None and usable_comps:
        point = 0.6 * formula + 0.4 * median(comps["_prices"])
        factors.append(f"Blended with the median of {comps['count']} {comps['scope']} on the platform "
                       f"(₹{comps['median']:,})")
    elif formula is not None:
        point = formula
    else:
        point = median(comps["_prices"])
        factors.append(f"Based on the median of {comps['count']} {comps['scope']} on the platform")

    # ---- 5. range + confidence
    strong_anchor = bool(purchase_price)
    if strong_anchor and age_known and usable_comps:
        confidence, spread = "high", 0.12
    elif (strong_anchor and age_known) or usable_comps:
        confidence, spread = "medium", 0.18
    else:
        confidence, spread = "low", 0.28

    return {
        "available": True,
        "point": _round_price(point),
        "low": _round_price(point * (1 - spread)),
        "high": _round_price(point * (1 + spread)),
        "currency": "INR",
        "confidence": confidence,
        "factors": factors,
        "comparables": {k: v for k, v in comps.items() if not k.startswith("_")},
        "reference": ({"category": ref.category, "typical_new_price": float(ref.typical_new_price),
                       "source": ref.source, "observed_at": ref.observed_at} if ref and not purchase_price else None),
        "disclaimer": "An estimate from the details you gave, not a market quote or a guaranteed price.",
    }


# ---------------------------------------------------------------- admin

def serialize_category(r: CategoryPrice) -> dict:
    return {
        "category": r.category, "kind": r.kind, "display_name": r.display_name,
        "typical_new_price": float(r.typical_new_price), "currency": r.currency,
        "annual_depreciation": float(r.annual_depreciation), "residual_floor": float(r.residual_floor),
        "source": r.source, "observed_at": r.observed_at, "updated_at": r.updated_at,
    }


def list_categories(db: Session) -> list[dict]:
    rows = db.query(CategoryPrice).order_by(CategoryPrice.kind.desc(), CategoryPrice.category).all()
    return [serialize_category(r) for r in rows]


def update_category(db: Session, admin: User, category: str, data) -> dict:
    row = db.query(CategoryPrice).filter(CategoryPrice.category == category).first()
    if not row:
        raise APIError("Unknown category", status_code=404)
    now = datetime.utcnow()
    if data.typical_new_price is not None:
        row.typical_new_price = Decimal(str(data.typical_new_price))
        note = (data.source_note or "").strip()
        row.source = f"Admin reference — {note}" if note else "Admin reference"
        row.observed_at = now
    if data.annual_depreciation is not None:
        row.annual_depreciation = Decimal(str(data.annual_depreciation))
    if data.residual_floor is not None:
        row.residual_floor = Decimal(str(data.residual_floor))
    row.updated_at, row.updated_by = now, admin.id
    db.commit()
    db.refresh(row)
    return serialize_category(row)
