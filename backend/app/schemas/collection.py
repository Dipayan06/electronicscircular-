"""Collection request schemas (FR-I)."""
import datetime

from pydantic import BaseModel, ConfigDict

from .quotation import DeviceBrief, ProviderBrief


class CollectionCreate(BaseModel):
    device_id: int
    collector_id: int
    address: str | None = None
    preferred_date: datetime.date | None = None


class CollectionStatusUpdate(BaseModel):
    status: str


class CollectionOut(BaseModel):
    id: int
    device_id: int
    collector_id: int
    address: str | None = None
    preferred_date: datetime.date | None = None
    status: str
    created_at: datetime.datetime
    device: DeviceBrief | None = None
    collector: ProviderBrief | None = None

    model_config = ConfigDict(from_attributes=True)
