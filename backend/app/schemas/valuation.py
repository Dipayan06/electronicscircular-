"""Resale-estimate schemas."""
from pydantic import BaseModel, Field


class EstimateIn(BaseModel):
    kind: str                                  # device | component
    type: str                                  # category (smartphone, gpu, …)
    device_id: int | None = None               # a registered device → uses its year + assessment
    purchase_price: float | None = Field(default=None, gt=0, le=1e8, allow_inf_nan=False)
    purchase_year: int | None = None
    condition: str | None = None


class CategoryPriceUpdateIn(BaseModel):
    typical_new_price: float | None = Field(default=None, gt=0, le=1e8, allow_inf_nan=False)
    source_note: str | None = Field(default=None, max_length=120)
    annual_depreciation: float | None = Field(default=None, ge=0, lt=1, allow_inf_nan=False)
    residual_floor: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
