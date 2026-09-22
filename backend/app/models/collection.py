"""Collection request model (FR-I)."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import COLLECTION_STATUS


class CollectionRequest(Base):
    __tablename__ = "collection_requests"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    collector_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    address = Column(String(255))
    preferred_date = Column(Date)
    status = Column(Enum(*COLLECTION_STATUS, name="collection_status", native_enum=False, create_constraint=True),
                    default="REQUESTED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    device = relationship("Device", back_populates="collection_requests")
    collector = relationship("Provider", back_populates="collection_requests")
