"""Material reference pricing (Feature 2) + price-band assessment (Feature 4).

Honesty rules this module enforces:
- No price is invented here. Values come either from an admin (clearly labelled
  "reference") or from the optional market-data feed configured via env.
- A value is only ever reported as `live` when it came from the feed AND is
  fresher than PRICE_STALE_AFTER_HOURS. Everything else is `reference` or `stale`.
- If the feed fails, the last-known value is kept, the error is recorded on the
  row, and the value keeps its original timestamp, so it ages into `stale`
  instead of being silently passed off as current.
"""
import math
import time
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import MaterialPrice, MaterialPriceHistory, User
from ..models.enums import MATERIAL_CATEGORIES, UNIT_GRAMS
from ..utils.responses import APIError

# ---------------------------------------------------------------- read cache
# Reference prices are read on every marketplace/listing-form render but change
# rarely, so the serialized list is cached briefly and dropped on any write.
_CACHE_TTL_SECONDS = 60
_cache: dict = {"at": 0.0, "data": None}


def _invalidate_cache() -> None:
    _cache["at"], _cache["data"] = 0.0, None


# ---------------------------------------------------------------- helpers

def price_status(row: MaterialPrice, now: datetime | None = None) -> str:
    """live | reference | stale — the label the UI must show next to a price."""
    now = now or datetime.utcnow()
    if now - row.observed_at > timedelta(hours=settings.PRICE_STALE_AFTER_HOURS):
        return "stale"
    return "live" if row.source_type == "api" else "reference"


def serialize(row: MaterialPrice) -> dict:
    return {
        "material": row.material,
        "display_name": row.display_name,
        "reference_price": float(row.reference_price),
        "currency": row.currency,
        "unit": row.unit,
        "source": row.source,
        "source_type": row.source_type,
        "status": price_status(row),
        "is_live": price_status(row) == "live",
        "observed_at": row.observed_at,
        "updated_at": row.updated_at,
        "last_fetch_error": row.last_fetch_error,
        "band_min": float(row.band_min),
        "band_max": float(row.band_max),
        "extreme_max": float(row.extreme_max),
    }


def _to_decimal(value, field: str) -> Decimal:
    """Parse a positive, finite decimal (rejects NaN/inf/negative/zero)."""
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise APIError(f"{field} must be a number", status_code=422)
    if not d.is_finite() or d <= 0:
        raise APIError(f"{field} must be a positive, finite number", status_code=422)
    return d


def _record_history(db: Session, row: MaterialPrice, user_id: int | None) -> None:
    db.add(MaterialPriceHistory(
        material=row.material, reference_price=row.reference_price, currency=row.currency,
        unit=row.unit, source=row.source, source_type=row.source_type,
        observed_at=row.observed_at, recorded_by=user_id,
    ))


def _get_row(db: Session, material: str) -> MaterialPrice:
    row = db.query(MaterialPrice).filter(MaterialPrice.material == material).first()
    if not row:
        raise APIError("No reference price for this material", status_code=404)
    return row


# ---------------------------------------------------------------- reads

def list_prices(db: Session) -> list[dict]:
    if _cache["data"] is not None and time.monotonic() - _cache["at"] < _CACHE_TTL_SECONDS:
        return _cache["data"]
    rows = db.query(MaterialPrice).order_by(MaterialPrice.material).all()
    data = [serialize(r) for r in rows]
    _cache["at"], _cache["data"] = time.monotonic(), data
    return data


def get_price(db: Session, material: str) -> dict:
    return serialize(_get_row(db, material))


def history(db: Session, material: str, limit: int = 50) -> list[dict]:
    _get_row(db, material)
    rows = (
        db.query(MaterialPriceHistory)
        .filter(MaterialPriceHistory.material == material)
        .order_by(MaterialPriceHistory.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return [{
        "reference_price": float(h.reference_price), "currency": h.currency, "unit": h.unit,
        "source": h.source, "source_type": h.source_type,
        "observed_at": h.observed_at, "recorded_at": h.recorded_at,
    } for h in rows]


# ---------------------------------------------------------------- admin writes

def set_reference(db: Session, admin: User, material: str, data) -> dict:
    """Admin sets/updates a material's reference price and/or regulation band."""
    row = _get_row(db, material)
    price_changed = False

    if data.reference_price is not None:
        row.reference_price = _to_decimal(data.reference_price, "reference_price")
        price_changed = True
    if data.unit is not None:
        if data.unit not in UNIT_GRAMS:
            raise APIError(f"unit must be one of {', '.join(UNIT_GRAMS)}", status_code=422)
        row.unit = data.unit
        price_changed = True

    band_min = _to_decimal(data.band_min, "band_min") if data.band_min is not None else row.band_min
    band_max = _to_decimal(data.band_max, "band_max") if data.band_max is not None else row.band_max
    extreme = _to_decimal(data.extreme_max, "extreme_max") if data.extreme_max is not None else row.extreme_max
    if not (Decimal(band_min) < 1 < Decimal(band_max) < Decimal(extreme)):
        raise APIError("Band must satisfy band_min < 1 < band_max < extreme_max", status_code=422)
    row.band_min, row.band_max, row.extreme_max = band_min, band_max, extreme

    now = datetime.utcnow()
    if price_changed:
        note = (data.source_note or "").strip()
        # An admin-entered value is always a *reference*, never a live price.
        row.source = f"Admin reference — {note}" if note else "Admin reference"
        row.source_type = "admin"
        row.observed_at = now
        row.last_fetch_error = None
        _record_history(db, row, admin.id)
    row.updated_at = now
    row.updated_by = admin.id
    db.commit()
    db.refresh(row)
    _invalidate_cache()
    return serialize(row)


# ---------------------------------------------------------------- market feed

def feed_configured() -> bool:
    return bool(settings.PRICE_API_BASE_URL)


def _fetch_from_feed(material: str) -> dict:
    """Fetch one material's price from the configured market-data provider.

    Expected response (adapt this function to the chosen provider):
        {"price": 812.5, "currency": "INR", "unit": "kg", "timestamp": "2026-09-25T10:00:00Z"}
    The API key is sent as a bearer header and never logged or returned.
    """
    headers = {"Authorization": f"Bearer {settings.PRICE_API_KEY}"} if settings.PRICE_API_KEY else {}
    url = f"{settings.PRICE_API_BASE_URL.rstrip('/')}/{material}"
    r = httpx.get(url, headers=headers, timeout=5.0)
    r.raise_for_status()
    body = r.json()
    price = float(body["price"])
    if not math.isfinite(price) or price <= 0:
        raise ValueError("feed returned a non-positive price")
    if body.get("currency", "INR") != "INR":
        raise ValueError("feed currency is not INR")
    unit = body.get("unit", "kg")
    if unit not in UNIT_GRAMS:
        raise ValueError(f"feed unit '{unit}' not supported")
    ts = body.get("timestamp")
    observed = (datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                if ts else datetime.utcnow())
    return {"price": Decimal(str(price)), "unit": unit, "observed_at": observed}


def refresh_from_feed(db: Session, admin: User) -> dict:
    """Pull every material from the feed. Failures keep the last-known value."""
    if not feed_configured():
        raise APIError("No market-data feed is configured (PRICE_API_BASE_URL). "
                       "Prices are admin-managed references.", status_code=400)
    results = {}
    for row in db.query(MaterialPrice).all():
        try:
            got = _fetch_from_feed(row.material)
            row.reference_price, row.unit, row.observed_at = got["price"], got["unit"], got["observed_at"]
            row.source = f"Market feed ({httpx.URL(settings.PRICE_API_BASE_URL).host})"
            row.source_type = "api"
            row.last_fetch_error = None
            row.updated_at, row.updated_by = datetime.utcnow(), admin.id
            _record_history(db, row, admin.id)
            results[row.material] = "updated"
        except Exception as exc:  # network, HTTP, parse — never fatal
            row.last_fetch_error = f"{datetime.utcnow():%Y-%m-%d %H:%M} UTC: {type(exc).__name__}"[:240]
            results[row.material] = "failed — kept last-known value"
    db.commit()
    _invalidate_cache()
    return results


# ---------------------------------------------------------------- Feature 4

def assess_price(db: Session, kind: str, material: str, unit: str | None, price: float) -> dict:
    """Classify a listing price against its material's reference band.

    Returns {level, reason, ratio, reference…}. Only material listings with a
    reference are regulated; devices/components/"other" are NORMAL (unregulated).
    """
    if not math.isfinite(price) or price <= 0:
        raise APIError("Price must be a positive, finite number", status_code=422)
    base = {"level": "NORMAL", "regulated": False, "ratio": None, "reference": None}

    if kind != "material" or material not in MATERIAL_CATEGORIES:
        return {**base, "reason": "No reference price applies to this category."}

    row = db.query(MaterialPrice).filter(MaterialPrice.material == material).first()
    if not row:
        return {**base, "reason": "No reference price has been set for this material yet."}
    ref = serialize(row)

    if unit not in UNIT_GRAMS:
        # Mass can't be compared (e.g. "piece"). Rather than let a unit switch
        # bypass regulation, route it to an admin.
        return {"level": "REVIEW", "regulated": True, "ratio": None, "reference": ref,
                "reason": f"Price per '{unit}' can't be compared to the reference "
                          f"(per {row.unit}); an admin will review it."}

    listed_per_g = Decimal(str(price)) / UNIT_GRAMS[unit]
    ref_per_g = row.reference_price / UNIT_GRAMS[row.unit]
    ratio = listed_per_g / ref_per_g
    r = float(round(ratio, 3))
    band = f"{float(row.band_min):g}×–{float(row.band_max):g}×"

    if ratio > row.extreme_max:
        level, reason = "EXTREME", (f"Price is {r:g}× the reference — above the {float(row.extreme_max):g}× "
                                    f"limit. The listing is held until an admin reviews it.")
    elif ratio > row.band_max:
        level, reason = "REVIEW", (f"Price is {r:g}× the reference (normal band {band}). "
                                   f"Add a justification; an admin will review it.")
    elif ratio < row.band_min:
        level, reason = "REVIEW", (f"Price is only {r:g}× the reference (normal band {band}). "
                                   f"Unusually low prices are reviewed to prevent fraud.")
    else:
        level, reason = "NORMAL", f"Price is within the normal band ({r:g}× the reference)."
    return {"level": level, "regulated": True, "ratio": r, "reference": ref, "reason": reason}
