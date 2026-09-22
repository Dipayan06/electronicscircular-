"""Provider, ProviderService and SparePart models (FR-E, FR-L)."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import PROVIDER_TYPES, DEVICE_TYPES


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True)
    # Optional link to the login account that operates this provider.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(140), nullable=False)
    type = Column(Enum(*PROVIDER_TYPES, name="provider_type", native_enum=False, create_constraint=True), nullable=False)
    location = Column(String(120))
    verified = Column(Boolean, default=False, nullable=False)
    rating = Column(Float, default=0.0)
    contact = Column(String(180))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="provider")
    service_items = relationship("ProviderService", back_populates="provider", cascade="all, delete-orphan")
    spare_parts = relationship("SparePart", back_populates="supplier", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="provider")
    bookings = relationship("Booking", back_populates="provider")
    collection_requests = relationship("CollectionRequest", back_populates="collector")


class ProviderService(Base):
    """A service offered by a provider (1:N) — normalized out of the provider row."""
    __tablename__ = "provider_services"

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)

    provider = relationship("Provider", back_populates="service_items")


class SparePart(Base):
    __tablename__ = "spare_parts"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    name = Column(String(140), nullable=False)
    device_type = Column(Enum(*DEVICE_TYPES, name="part_device_type", native_enum=False, create_constraint=True))
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    supplier = relationship("Provider", back_populates="spare_parts")
