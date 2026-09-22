"""Pydantic schemas for resale listings."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..models.enums import DEVICE_TYPES


class ListingCreate(BaseModel):
    device_id: int | None = None
    title: str = Field(min_length=2, max_length=160)
    type: str
    price: float = Field(gt=0)
    condition: str | None = None
    description: str | None = None

    @field_validator("type")
    @classmethod
    def valid_type(cls, v):
        if v not in DEVICE_TYPES:
            raise ValueError(f"must be one of {', '.join(DEVICE_TYPES)}")
        return v


class ListingOut(BaseModel):
    id: int
    title: str
    type: str
    price: float
    condition: str | None = None
    description: str | None = None
    status: str
    seller_id: int
    seller: str | None = None
    device_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_listing(cls, listing) -> "ListingOut":
        return cls(
            id=listing.id, title=listing.title, type=listing.type, price=listing.price,
            condition=listing.condition, description=listing.description, status=listing.status,
            seller_id=listing.seller_id, seller=listing.seller.name if listing.seller else None,
            device_id=listing.device_id, created_at=listing.created_at,
        )
