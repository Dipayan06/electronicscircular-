"""Resale listing business logic (service layer)."""
from sqlalchemy.orm import Session

from ..models import ResaleListing, Device, User
from ..schemas.listing import ListingOut, ListingCreate
from ..utils.responses import APIError
from . import lifecycle_service


def list_listings(db: Session, kind_filter: str | None = None) -> list[ListingOut]:
    """List marketplace items, optionally filtered by kind (device/component/material)."""
    query = db.query(ResaleListing)
    if kind_filter and kind_filter != "all":
        query = query.filter(ResaleListing.kind == kind_filter)
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

    payload = data.model_dump()
    # Devices/components default to a single unit if no quantity given.
    if payload.get("quantity") is None:
        payload["quantity"] = 1
    listing = ResaleListing(seller_id=user.id, status="ACTIVE", **payload)
    db.add(listing)
    db.flush()
    if listing.device_id:
        lifecycle_service.log_event(db, listing.device_id, "LISTED_FOR_RESALE",
                                    f"Listed for resale at ₹{int(listing.price):,}", user.name)
    db.commit()
    db.refresh(listing)
    return ListingOut.from_orm_listing(listing)


def reserve_listing(db: Session, user: User, listing_id: int, quantity: float | None = None) -> ListingOut:
    """Simulated purchase/reservation (no real payment — FR-H4).

    For material listings the buyer specifies a quantity; the requested amount is
    deducted from the available stock (buy in appropriate quantities or in bulk).
    Devices/components are reserved whole.
    """
    listing = db.query(ResaleListing).filter(ResaleListing.id == listing_id).first()
    if not listing:
        raise APIError("Listing not found", status_code=404)
    if listing.status != "ACTIVE":
        raise APIError("This listing is no longer available", status_code=400)

    if listing.kind == "material":
        available = listing.quantity or 0
        qty = quantity if quantity is not None else (listing.min_order or available)
        if qty <= 0:
            raise APIError("Enter a quantity to buy", status_code=400)
        if listing.min_order and qty < listing.min_order:
            raise APIError(f"Minimum order is {listing.min_order:g} {listing.unit}", status_code=400)
        if qty > available:
            raise APIError(f"Only {available:g} {listing.unit} available", status_code=400)
        listing.quantity = available - qty
        # Sold out (or below the minimum order) → close the listing.
        if listing.quantity <= 0 or (listing.min_order and listing.quantity < listing.min_order):
            listing.status = "SOLD"
    else:
        listing.status = "RESERVED"
        if listing.device_id:
            lifecycle_service.log_event(db, listing.device_id, "RESERVED",
                                        "Reserved by a buyer on the marketplace", user.name)

    db.commit()
    db.refresh(listing)
    return ListingOut.from_orm_listing(listing)
