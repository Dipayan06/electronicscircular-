"""Notification model (Feature 3). Persistent, per-user, in-app notifications."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(40), default="system", nullable=False)  # order|price|verification|system…
    title = Column(String(140), nullable=False)
    message = Column(String(400), nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime)
    meta = Column("metadata", JSON)          # optional structured payload (ids, links)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")
