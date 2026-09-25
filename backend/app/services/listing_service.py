"""Resale listing business logic (service layer)."""
from sqlalchemy.orm import Session

from ..models import ResaleListing, Device, User
from ..schemas.listing import ListingOut, ListingCreate
from ..utils.responses import APIError
from . import lifecycle_service, notification_service, pricing_service, price_review_service

# Listings the public marketplace never shows (Feature 4). PRICE_REVIEW_REQUIRED
# stays visible (badged, not purchasable); EXTREME/REJECTED are hidden.
_HIDDEN_STATUSES = ("SUSPENDED_PENDING_REVIEW", "REJECTED")


def list_listings(db: Session, kind_filter: str | None = None) -> list[ListingOut]:
    """List marketplace items, optionally filtered by kind (device/component/material)."""
    query = db.query(ResaleListing).filter(ResaleListing.status.notin_(_HIDDEN_STATUSES))
    if kind_filter and kind_filter != "all":
        query = query.filter(ResaleListing.kind == kind_filter)
    listings = query.order_by(ResaleListing.created_at.desc()).all()
    return [ListingOut.from_orm_listing(l) for l in listings]


def list_mine(db: Session, user: User) -> list[ListingOut]:
    """The seller's own listings, including ones held for price review."""
    listings = (db.query(ResaleListing).filter(ResaleListing.seller_id == user.id)
                .order_by(ResaleListing.created_at.desc()).all())
    return [ListingOut.from_orm_listing(l) for l in listings]


def get_listing(db: Session, listing_id: int, viewer: User | None = None) -> ListingOut:
    listing = db.query(ResaleListing).filter(ResaleListing.id == listing_id).first()
    # Hidden listings are visible only to their seller and admins (no leaking
    # suspended/rejected listings by guessing ids).
    if listing and listing.status in _HIDDEN_STATUSES:
        allowed = viewer is not None and (viewer.id == listing.seller_id or viewer.role.name == "admin")
        if not allowed:
            listing = None
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

    payload = data.model_dump(exclude={"price_justification"})
    # Devices/components default to a single unit if no quantity given.
    if payload.get("quantity") is None:
        payload["quantity"] = 1

    # Feature 4: server-side price regulation. The client's own preview is only
    # a hint — the level is recomputed here from the stored reference band.
    assessment = pricing_service.assess_price(db, data.kind, data.type, data.unit, data.price)
    justification = (data.price_justification or "").strip()
    if assessment["level"] == "REVIEW" and len(justification) < 10:
        raise APIError("This price is outside the normal range. Add a justification "
                       "(at least 10 characters) so an admin can review it.", status_code=422)
    status = {"NORMAL": "ACTIVE", "REVIEW": "PRICE_REVIEW_REQUIRED",
              "EXTREME": "SUSPENDED_PENDING_REVIEW"}[assessment["level"]]

    listing = ResaleListing(seller_id=user.id, status=status, **payload)
    db.add(listing)
    db.flush()
    if status != "ACTIVE":
        price_review_service.open_review(db, listing, assessment, justification)
    if listing.device_id:
        lifecycle_service.log_event(db, listing.device_id, "LISTED_FOR_RESALE",
                                    f"Listed for resale at ₹{int(listing.price):,}", user.name)
    db.commit()
    db.refresh(listing)
    return ListingOut.from_orm_listing(listing, assessment)


def reserve_listing(db: Session, user: User, listing_id: int, quantity: float | None = None) -> ListingOut:
    """Simulated purchase/reservation (no real payment — FR-H4).

    For material listings the buyer specifies a quantity; the requested amount is
    deducted from the available stock (buy in appropriate quantities or in bulk).
    Devices/components are reserved whole.
    """
    listing = db.query(ResaleListing).filter(ResaleListing.id == listing_id).first()
    if not listing:
        raise APIError("Listing not found", status_code=404)
    if listing.status in ("PRICE_REVIEW_REQUIRED", "SUSPENDED_PENDING_REVIEW"):
        raise APIError("This listing's price is under review and can't be bought yet", status_code=400)
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

    # Notify the seller (new order) and the buyer (confirmation).
    bought = f"{quantity:g} {listing.unit} of " if listing.kind == "material" and quantity else ""
    notification_service.notify(db, listing.seller_id, "order", "New order received",
                                f"{user.name} purchased {bought}{listing.title}.", commit=False)
    if listing.seller_id != user.id:
        notification_service.notify(db, user.id, "order", "Purchase confirmed",
                                    f"You purchased {bought}{listing.title}.", commit=False)
    db.commit()
    db.refresh(listing)
    return ListingOut.from_orm_listing(listing)
