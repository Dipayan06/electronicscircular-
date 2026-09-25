"""Material reference pricing + price regulation models (Features 2 + 4).

`MaterialPrice` holds ONE current reference price per material. Money is stored
as Numeric (exact decimal), never float. Every value records where it came from
(`source`, `source_type`) and when it was observed (`observed_at`), so the UI can
label it honestly — an admin-set reference is never presented as a live price.

`MaterialPriceHistory` is an append-only log of every reference change (audit).

`PriceReview` is the audit trail for Feature 4: one row per listing whose price
fell outside the normal band, with the snapshot used to judge it, the seller's
justification and the admin decision.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import MATERIAL_CATEGORIES, PRICE_SOURCE_TYPES, PRICE_LEVELS, PRICE_REVIEW_STATUS, CURRENCIES


class MaterialPrice(Base):
    __tablename__ = "material_prices"

    id = Column(Integer, primary_key=True)
    material = Column(Enum(*MATERIAL_CATEGORIES, name="price_material", native_enum=False, create_constraint=True),
                      unique=True, nullable=False)
    display_name = Column(String(60), nullable=False)
    reference_price = Column(Numeric(14, 4), nullable=False)   # per `unit`, in `currency`
    currency = Column(Enum(*CURRENCIES, name="price_currency", native_enum=False, create_constraint=True),
                      default="INR", nullable=False)
    unit = Column(String(12), nullable=False)                  # g | kg | tonne
    source = Column(String(160), nullable=False)               # human-readable provenance
    source_type = Column(Enum(*PRICE_SOURCE_TYPES, name="price_source_type", native_enum=False,
                              create_constraint=True), default="admin", nullable=False)
    observed_at = Column(DateTime, nullable=False)             # when the price was true at the source
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # last write to this row
    updated_by = Column(Integer, ForeignKey("users.id"))
    last_fetch_error = Column(String(240))                     # last feed failure (kept, not hidden)

    # Feature 4 band, as multipliers of the reference price:
    #   band_min ≤ ratio ≤ band_max → NORMAL
    #   ratio < band_min, or band_max < ratio ≤ extreme_max → REVIEW
    #   ratio > extreme_max → EXTREME
    band_min = Column(Numeric(6, 3), default=0.5, nullable=False)
    band_max = Column(Numeric(6, 3), default=1.5, nullable=False)
    extreme_max = Column(Numeric(6, 3), default=3.0, nullable=False)


class MaterialPriceHistory(Base):
    __tablename__ = "material_price_history"

    id = Column(Integer, primary_key=True)
    material = Column(String(20), nullable=False, index=True)
    reference_price = Column(Numeric(14, 4), nullable=False)
    currency = Column(String(3), nullable=False)
    unit = Column(String(12), nullable=False)
    source = Column(String(160), nullable=False)
    source_type = Column(String(10), nullable=False)
    observed_at = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id"))


class PriceReview(Base):
    __tablename__ = "price_reviews"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("resale_listings.id"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    material = Column(String(20), nullable=False)
    level = Column(Enum(*PRICE_LEVELS, name="price_level", native_enum=False, create_constraint=True),
                   nullable=False)
    # Snapshot of what the decision was based on (so later reference changes
    # don't rewrite history).
    listed_price = Column(Numeric(14, 4), nullable=False)
    listed_unit = Column(String(12))
    reference_price = Column(Numeric(14, 4))
    reference_unit = Column(String(12))
    ratio = Column(Numeric(10, 3))
    reason = Column(String(300), nullable=False)
    justification = Column(String(600))
    status = Column(Enum(*PRICE_REVIEW_STATUS, name="price_review_status", native_enum=False,
                         create_constraint=True), default="PENDING", nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewer_note = Column(String(400))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    decided_at = Column(DateTime)

    listing = relationship("ResaleListing")
    seller = relationship("User", foreign_keys=[seller_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
