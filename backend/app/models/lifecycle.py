"""Lifecycle event model (FR-J) — the Digital Device Passport store.

Append-only audit trail. Every mutating service writes here (Phase 1 §1.3), and
the timeline is read back for a device. `meta` maps to the "metadata" column
(the attribute name `metadata` is reserved by SQLAlchemy's declarative Base).
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..database import Base


class LifecycleEvent(Base):
    __tablename__ = "lifecycle_events"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    type = Column(String(60), nullable=False)        # e.g. DEVICE_REGISTERED, CONDITION_ASSESSED
    description = Column(String(300), nullable=False)
    actor = Column(String(120))                      # who caused the event
    meta = Column("metadata", JSON, nullable=True)   # optional structured detail
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    device = relationship("Device", back_populates="lifecycle_events")
