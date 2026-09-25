"""Pydantic schemas for marketplace listings (devices, components, materials)."""
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

from ..models.enums import LISTING_KINDS, MATERIAL_UNITS, categories_for_kind


class ListingCreate(BaseModel):
    kind: str = "device"                 # device | component | material
    type: str                            # category within the kind
    title: str = Field(min_length=2, max_length=160)
    price: float = Field(gt=0)           # total price, or price-per-unit for materials
    condition: str | None = None
    description: str | None = None
    device_id: int | None = None         # only for whole-device listings

    # Quantity-based fields (required for materials).
    unit: str | None = None
    quantity: float | None = None
    min_order: float | None = None

    @model_validator(mode="after")
    def _validate(self):
        if self.kind not in LISTING_KINDS:
            raise ValueError(f"kind must be one of {', '.join(LISTING_KINDS)}")
        allowed = categories_for_kind(self.kind)
        if self.type not in allowed:
            raise ValueError(f"type must be one of {', '.join(allowed)} for a {self.kind}")
        if self.kind == "material":
            if not self.unit or self.unit not in MATERIAL_UNITS:
                raise ValueError(f"materials need a unit ({', '.join(MATERIAL_UNITS)})")
            if not self.quantity or self.quantity <= 0:
                raise ValueError("materials need a positive available quantity")
            if self.min_order is not None and self.min_order <= 0:
                raise ValueError("min_order must be positive")
        return self


class ReserveIn(BaseModel):
    """Purchase/reserve request. Materials specify how much to buy."""
    quantity: float | None = None


class ListingOut(BaseModel):
    id: int
    kind: str
    type: str
    title: str
    price: float
    unit: str | None = None
    quantity: float | None = None
    min_order: float | None = None
    condition: str | None = None
    description: str | None = None
    status: str
    seller_id: int
    seller: str | None = None
    device_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_listing(cls, l) -> "ListingOut":
        return cls(
            id=l.id, kind=l.kind, type=l.type, title=l.title, price=l.price,
            unit=l.unit, quantity=l.quantity, min_order=l.min_order,
            condition=l.condition, description=l.description, status=l.status,
            seller_id=l.seller_id, seller=l.seller.name if l.seller else None,
            device_id=l.device_id, created_at=l.created_at,
        )
