"""User & Role models (FR-A). A user has exactly one role (Phase 0 assumption A1)."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import ROLES


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(Enum(*ROLES, name="role_name", native_enum=False, create_constraint=True), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(180), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    # Email verification state (Feature 1). Server-authoritative — the frontend
    # cannot flip this; only a valid OTP verification sets it True.
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    role = relationship("Role", back_populates="users")

    # A user owns devices and marketplace listings.
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")
    listings = relationship("ResaleListing", back_populates="seller")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    # Optional link to a provider profile (for provider-role accounts).
    provider = relationship("Provider", back_populates="user", uselist=False)
