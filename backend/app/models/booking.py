"""Booking model (FR-G). Created from an accepted quotation (1:1)."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import BOOKING_STATUS


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), unique=True, nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    date = Column(Date)
    service_type = Column(String(80))
    address = Column(String(255))
    notes = Column(String(500))
    status = Column(Enum(*BOOKING_STATUS, name="booking_status", native_enum=False, create_constraint=True),
                    default="REQUESTED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    quotation = relationship("Quotation", back_populates="booking")
    device = relationship("Device", back_populates="bookings")
    provider = relationship("Provider", back_populates="bookings")
