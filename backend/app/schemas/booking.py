"""Booking schemas (FR-G)."""
import datetime

from pydantic import BaseModel, ConfigDict

from .quotation import DeviceBrief, ProviderBrief


class BookingCreate(BaseModel):
    quotation_id: int
    date: datetime.date | None = None
    service_type: str | None = "Repair"
    address: str | None = None
    notes: str | None = None


class BookingStatusUpdate(BaseModel):
    status: str


class BookingOut(BaseModel):
    id: int
    quotation_id: int | None = None
    device_id: int
    provider_id: int
    date: datetime.date | None = None
    service_type: str | None = None
    address: str | None = None
    notes: str | None = None
    status: str
    created_at: datetime.datetime
    device: DeviceBrief | None = None
    provider: ProviderBrief | None = None

    model_config = ConfigDict(from_attributes=True)
