"""Resale listing model (FR-H)."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import DEVICE_TYPES, LISTING_STATUS


class ResaleListing(Base):
    __tablename__ = "resale_listings"

    id = Column(Integer, primary_key=True)
    # Optional link to a registered device; external listings may have none.
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    type = Column(Enum(*DEVICE_TYPES, name="listing_type", native_enum=False, create_constraint=True), nullable=False)
    price = Column(Float, nullable=False)
    condition = Column(String(40))
    description = Column(String(600))
    status = Column(Enum(*LISTING_STATUS, name="listing_status", native_enum=False, create_constraint=True),
                    default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    seller = relationship("User", back_populates="listings")
    device = relationship("Device")
