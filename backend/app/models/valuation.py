"""Device/component valuation reference (resale-estimate feature).

`CategoryPrice` holds an admin-managed *typical new price* per device/component
category plus how fast that category loses value. It is only a fallback anchor
for the resale estimate when the seller doesn't say what they paid — it is
labelled as an admin reference, never as market data. Money is Numeric.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum

from ..database import Base
from .enums import DEVICE_CATEGORIES, COMPONENT_CATEGORIES

VALUED_CATEGORIES = DEVICE_CATEGORIES + COMPONENT_CATEGORIES


class CategoryPrice(Base):
    __tablename__ = "category_prices"

    id = Column(Integer, primary_key=True)
    category = Column(Enum(*VALUED_CATEGORIES, name="valued_category", native_enum=False, create_constraint=True),
                      unique=True, nullable=False)
    kind = Column(String(12), nullable=False)                 # device | component
    display_name = Column(String(60), nullable=False)
    typical_new_price = Column(Numeric(12, 2), nullable=False)  # INR, typical price when new
    currency = Column(String(3), default="INR", nullable=False)
    # Fraction of value lost per year of age (compounding), and the floor below
    # which a working item's value is not depreciated further.
    annual_depreciation = Column(Numeric(4, 3), nullable=False)
    residual_floor = Column(Numeric(4, 3), default=0.1, nullable=False)
    source = Column(String(160), nullable=False)
    observed_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
