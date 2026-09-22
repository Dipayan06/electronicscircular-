"""Device schemas (FR-B). Pydantic validates input at the API boundary."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..models.enums import DEVICE_TYPES, WORKING_STATUS


class DeviceCreate(BaseModel):
    type: str
    brand: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=120)
    serial: str | None = None
    purchase_year: int | None = Field(default=None, ge=2005, le=datetime.utcnow().year)
    working_status: str = "working"
    accessories: str | None = None

    @field_validator("type")
    @classmethod
    def valid_type(cls, v):
        if v not in DEVICE_TYPES:
            raise ValueError(f"must be one of {', '.join(DEVICE_TYPES)}")
        return v

    @field_validator("working_status")
    @classmethod
    def valid_status(cls, v):
        if v not in WORKING_STATUS:
            raise ValueError(f"must be one of {', '.join(WORKING_STATUS)}")
        return v


class DeviceUpdate(BaseModel):
    """All fields optional — only the provided ones are updated."""
    brand: str | None = None
    model: str | None = None
    serial: str | None = None
    purchase_year: int | None = Field(default=None, ge=2005, le=datetime.utcnow().year)
    working_status: str | None = None
    accessories: str | None = None

    @field_validator("working_status")
    @classmethod
    def valid_status(cls, v):
        if v is not None and v not in WORKING_STATUS:
            raise ValueError(f"must be one of {', '.join(WORKING_STATUS)}")
        return v


class DeviceOut(BaseModel):
    id: int
    type: str
    brand: str
    model: str
    serial: str | None = None
    purchase_year: int | None = None
    working_status: str
    accessories: str | None = None
    recommendation: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
