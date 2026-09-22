"""Booking endpoints (FR-G). All protected."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.booking import BookingCreate, BookingStatusUpdate
from ..services import booking_service
from ..utils.responses import success

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", summary="List my bookings (consumer) / job board (provider)")
def list_bookings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(booking_service.list_bookings(db, user), "Bookings retrieved")


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a booking from an accepted quote")
def create_booking(data: BookingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(booking_service.create_booking(db, user, data), "Booking confirmed")


@router.put("/{booking_id}/status", summary="Update booking status (provider)")
def update_status(booking_id: int, data: BookingStatusUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(booking_service.update_status(db, user, booking_id, data.status), "Booking updated")
