"""Pricing + price-review schemas (Features 2 + 4)."""
from pydantic import BaseModel, Field


class PriceUpdateIn(BaseModel):
    """Admin update of a material's reference price and/or regulation band.
    All fields optional; numbers must be positive and finite (checked again in
    the service using exact Decimal arithmetic)."""
    reference_price: float | None = Field(default=None, gt=0, le=1e9, allow_inf_nan=False)
    unit: str | None = None
    source_note: str | None = Field(default=None, max_length=120)
    band_min: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    band_max: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    extreme_max: float | None = Field(default=None, gt=0, allow_inf_nan=False)


class PriceCheckIn(BaseModel):
    """Seller-side preview of how a price will be classified (advisory only —
    the same check is re-run authoritatively when the listing is created)."""
    kind: str
    type: str
    unit: str | None = None
    price: float = Field(gt=0, le=1e9, allow_inf_nan=False)


class ReviewDecisionIn(BaseModel):
    note: str | None = Field(default=None, max_length=400)
