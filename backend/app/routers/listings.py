"""Marketplace listing endpoints (FR-H). Reads are public; create/reserve require
authentication. Listings can be devices, components, or materials sold by quantity."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user, get_optional_user, require_verified
from ..models import User
from ..schemas.listing import ListingCreate, ReserveIn
from ..services import listing_service
from ..utils.responses import success

router = APIRouter(prefix="/listings", tags=["Marketplace"])


@router.get("", summary="List marketplace items (optional ?kind= device|component|material)")
def list_listings(kind: str | None = Query(default=None), db: Session = Depends(get_db)):
    return success(listing_service.list_listings(db, kind), "Listings retrieved")


@router.post("", status_code=status.HTTP_201_CREATED, summary="List a device, component or material for sale")
def create_listing(data: ListingCreate, db: Session = Depends(get_db), user: User = Depends(require_verified)):
    return success(listing_service.create_listing(db, user, data), "Item listed for sale")


@router.get("/mine", summary="My listings, including ones held for price review")
def my_listings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(listing_service.list_mine(db, user), "Your listings")


@router.get("/{listing_id}", summary="Get one listing")
def get_listing(listing_id: int, db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user)):
    return success(listing_service.get_listing(db, listing_id, viewer), "Listing retrieved")


@router.put("/{listing_id}/reserve", summary="Buy/reserve a listing (materials take a quantity)")
def reserve_listing(listing_id: int, data: ReserveIn | None = None,
                    db: Session = Depends(get_db), user: User = Depends(require_verified)):
    qty = data.quantity if data else None
    return success(listing_service.reserve_listing(db, user, listing_id, qty), "Purchase confirmed")
