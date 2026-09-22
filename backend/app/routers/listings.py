"""Marketplace listing endpoints (FR-H). Reads are public; create/reserve require
authentication."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.listing import ListingCreate
from ..services import listing_service
from ..utils.responses import success

router = APIRouter(prefix="/listings", tags=["Marketplace"])


@router.get("", summary="List resale listings (optional ?type= filter)")
def list_listings(type: str | None = Query(default=None), db: Session = Depends(get_db)):
    return success(listing_service.list_listings(db, type), "Listings retrieved")


@router.post("", status_code=status.HTTP_201_CREATED, summary="List a device for resale")
def create_listing(data: ListingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(listing_service.create_listing(db, user, data), "Device listed for resale")


@router.get("/{listing_id}", summary="Get one listing")
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    return success(listing_service.get_listing(db, listing_id), "Listing retrieved")


@router.put("/{listing_id}/reserve", summary="Reserve a listing (simulated purchase)")
def reserve_listing(listing_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(listing_service.reserve_listing(db, user, listing_id), "Listing reserved")
