"""Marketplace listing model (FR-H, extended).

A listing can be a whole **device**, an individual **component** (RAM, GPU, CPU,
motherboard, storage, cooler, …), or a recovered **material** (rare-earth metals,
silicon, copper, aluminium, gold, …) sold by quantity so buyers can purchase in
appropriate amounts or in bulk.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import LISTING_KINDS, LISTING_CATEGORIES, MATERIAL_UNITS, LISTING_STATUS


class ResaleListing(Base):
    __tablename__ = "resale_listings"

    id = Column(Integer, primary_key=True)
    # Optional link to a registered device; component/material listings have none.
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    kind = Column(Enum(*LISTING_KINDS, name="listing_kind", native_enum=False, create_constraint=True),
                  default="device", nullable=False)
    # Specific category within the kind (e.g. laptop / ram / copper / other).
    type = Column(Enum(*LISTING_CATEGORIES, name="listing_type", native_enum=False, create_constraint=True),
                  nullable=False)

    title = Column(String(160), nullable=False)
    # For device/component: total price. For material: price PER UNIT.
    price = Column(Float, nullable=False)

    # Quantity-based selling (materials, or multiple identical components).
    unit = Column(String(12))              # material: g | kg | tonne | piece
    quantity = Column(Float, default=1)    # available amount (units)
    min_order = Column(Float)              # material: minimum purchasable quantity

    condition = Column(String(40))
    description = Column(String(600))
    status = Column(Enum(*LISTING_STATUS, name="listing_status", native_enum=False, create_constraint=True),
                    default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    seller = relationship("User", back_populates="listings")
    device = relationship("Device")
