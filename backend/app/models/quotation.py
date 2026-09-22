"""Quotation model (FR-F). Device N:1 ... 1:N Provider, with a status lifecycle."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import QUOTATION_STATUS


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    problem = Column(String(500), nullable=False)
    cost = Column(Float)          # null until the provider quotes
    days = Column(Integer)        # estimated completion time
    description = Column(String(500))
    status = Column(Enum(*QUOTATION_STATUS, name="quotation_status", native_enum=False, create_constraint=True),
                    default="PENDING", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    device = relationship("Device", back_populates="quotations")
    provider = relationship("Provider", back_populates="quotations")
    # A quote maps to at most one booking (1:1) once accepted.
    booking = relationship("Booking", back_populates="quotation", uselist=False)
