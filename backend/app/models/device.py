"""Device & DeviceAssessment models (FR-B, FR-C)."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import DEVICE_TYPES, WORKING_STATUS, RECOMMENDATIONS


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(*DEVICE_TYPES, name="device_type", native_enum=False, create_constraint=True), nullable=False)
    brand = Column(String(80), nullable=False)
    model = Column(String(120), nullable=False)
    serial = Column(String(120))
    purchase_year = Column(Integer)
    working_status = Column(Enum(*WORKING_STATUS, name="working_status", native_enum=False, create_constraint=True),
                            default="working", nullable=False)
    accessories = Column(String(255))
    # Latest circularity recommendation (null until assessed) — FR-D.
    recommendation = Column(Enum(*RECOMMENDATIONS, name="recommendation", native_enum=False, create_constraint=True))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="devices")
    assessments = relationship("DeviceAssessment", back_populates="device", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="device", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="device", cascade="all, delete-orphan")
    lifecycle_events = relationship("LifecycleEvent", back_populates="device", cascade="all, delete-orphan")
    collection_requests = relationship("CollectionRequest", back_populates="device", cascade="all, delete-orphan")


class DeviceAssessment(Base):
    __tablename__ = "device_assessments"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    screen = Column(String(20), nullable=False)   # good | minor | cracked
    battery = Column(String(20), nullable=False)  # good | weak  | dead
    body = Column(String(20), nullable=False)     # good | scratched | damaged
    powers_on = Column(Boolean, default=True, nullable=False)
    charging = Column(Boolean, default=True, nullable=False)
    water_damage = Column(Boolean, default=False, nullable=False)
    problems = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    device = relationship("Device", back_populates="assessments")
