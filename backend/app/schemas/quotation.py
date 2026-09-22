"""Quotation schemas (FR-F) with brief nested device/provider for display."""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DeviceBrief(BaseModel):
    id: int
    brand: str
    model: str
    type: str
    model_config = ConfigDict(from_attributes=True)


class ProviderBrief(BaseModel):
    id: int
    name: str
    type: str
    model_config = ConfigDict(from_attributes=True)


class QuotationCreate(BaseModel):
    device_id: int
    provider_id: int
    problem: str = Field(min_length=3, max_length=500)


class QuoteSubmit(BaseModel):
    """Provider fills in the estimate."""
    cost: float = Field(gt=0)
    days: int = Field(ge=0)
    description: str | None = None


class QuotationOut(BaseModel):
    id: int
    device_id: int
    provider_id: int
    problem: str
    cost: float | None = None
    days: int | None = None
    description: str | None = None
    status: str
    created_at: datetime
    device: DeviceBrief | None = None
    provider: ProviderBrief | None = None

    model_config = ConfigDict(from_attributes=True)
