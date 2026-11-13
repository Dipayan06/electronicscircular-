"""Product photos for marketplace listings.

Images are stored in the database (not on disk) so they survive redeploys on
hosts with an ephemeral filesystem, such as Render's free tier. The bytes column
is deferred: loading a listing never pulls image data, only the image ids.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import deferred

from ..database import Base


class ListingImage(Base):
    __tablename__ = "listing_images"
    # Never reuse a deleted image's id (SQLite reuses the max rowid otherwise).
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("resale_listings.id"), nullable=False, index=True)
    content_type = Column(String(20), nullable=False)   # image/jpeg | image/png | image/webp
    data = deferred(Column(LargeBinary, nullable=False))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
