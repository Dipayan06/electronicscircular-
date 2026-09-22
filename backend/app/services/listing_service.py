"""Resale listing business logic (service layer)."""
from sqlalchemy.orm import Session

from ..models import ResaleListing, Device, User
from ..schemas.listing import ListingOut, ListingCreate
from ..utils.responses import APIError
from . import lifecycle_service


def list_listings(db: Session, type_filter: str | None = None) -> list[ListingOut]:
    query = db.query(ResaleListing)
    if type_filter and type_filter != "all":
        query = query.filter(ResaleListing.type == type_filter)
    listings = query.order_by(ResaleListing.created_at.desc()).all()
    return [ListingOut.from_orm_listing(l) for l in listings]


def get_listing(db: Session, listing_id: int) -> ListingOut:
    listing = db.query(ResaleListing).filter(ResaleListing.id == listing_id).first()
    if not listing:
        raise APIError("Listing not found", status_code=404)
    return ListingOut.from_orm_listing(listing)


def create_listing(db: Session, user: User, data: ListingCreate) -> ListingOut:
    # If linked to a registered device, the seller must own it.
    if data.device_id is not None:
        device = db.query(Device).filter(
            Device.id == data.device_id, Device.owner_id == user.id
        ).first()
        if not device:
            raise APIError("Device not found", status_code=404)

    listing = ResaleListing(seller_id=user.id, status="ACTIVE", **data.model_dump())
    db.add(listing)
    db.flush()
    if listing.device_id:
        lifecycle_service.log_event(db, listing.device_id, "LISTED_FOR_RESALE",
                                    f"Listed for resale at ₹{int(listing.price):,}", user.name)
    db.commit()
    db.refresh(listing)
    return ListingOut.from_orm_listing(listing)


def reserve_listing(db: Session, user: User, listing_id: int) -> ListingOut:
    """Simulated reservation (no real payment — FR-H4)."""
    listing = db.query(ResaleListing).filter(ResaleListing.id == listing_id).first()
    if not listing:
        raise APIError("Listing not found", status_code=404)
    if listing.status != "ACTIVE":
        raise APIError("This listing is no longer available", status_code=400)

    listing.status = "RESERVED"
    if listing.device_id:
        lifecycle_service.log_event(db, listing.device_id, "RESERVED",
                                    "Reserved by a buyer on the marketplace", user.name)
    db.commit()
    db.refresh(listing)
    return ListingOut.from_orm_listing(listing)
