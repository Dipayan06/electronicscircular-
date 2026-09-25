"""Booking business logic (FR-G). A booking originates from an accepted quotation
and moves through a validated status lifecycle."""
from sqlalchemy.orm import Session

from ..models import Booking, Quotation, Device, Provider, User
from ..schemas.booking import BookingCreate, BookingOut
from ..models.enums import BOOKING_STATUS
from ..utils.responses import APIError
from . import lifecycle_service, notification_service

PROVIDER_ROLES = ("provider", "refurbisher", "recycler", "supplier")


def _current_provider(db: Session, user: User) -> Provider | None:
    return db.query(Provider).filter(Provider.user_id == user.id).first()


def list_bookings(db: Session, user: User) -> list[BookingOut]:
    query = db.query(Booking)
    provider = _current_provider(db, user)
    if user.role.name in PROVIDER_ROLES and provider:
        query = query.filter(Booking.provider_id == provider.id)
    else:
        device_ids = [d.id for d in db.query(Device).filter(Device.owner_id == user.id).all()]
        if not device_ids:
            return []
        query = query.filter(Booking.device_id.in_(device_ids))
    bookings = query.order_by(Booking.created_at.desc()).all()
    return [BookingOut.model_validate(b) for b in bookings]


def create_booking(db: Session, user: User, data: BookingCreate) -> BookingOut:
    quote = db.query(Quotation).filter(Quotation.id == data.quotation_id).first()
    if not quote:
        raise APIError("Quotation not found", status_code=404)
    # The device on the quote must belong to the acting user.
    device = db.query(Device).filter(
        Device.id == quote.device_id, Device.owner_id == user.id
    ).first()
    if not device:
        raise APIError("Quotation not found", status_code=404)
    if quote.status != "ACCEPTED":
        raise APIError("A booking can only be created from an accepted quotation", status_code=400)
    if quote.booking is not None:
        raise APIError("This quotation is already booked", status_code=400)

    booking = Booking(
        quotation_id=quote.id, device_id=quote.device_id, provider_id=quote.provider_id,
        date=data.date, service_type=data.service_type, address=data.address,
        notes=data.notes, status="CONFIRMED",
    )
    db.add(booking)
    db.flush()
    provider = db.query(Provider).filter(Provider.id == quote.provider_id).first()
    lifecycle_service.log_event(db, device.id, "BOOKING_CONFIRMED",
                                f"Repair booking confirmed with {provider.name}", user.name)
    db.commit()
    db.refresh(booking)
    return BookingOut.model_validate(booking)


def update_status(db: Session, user: User, booking_id: int, new_status: str) -> BookingOut:
    if new_status not in BOOKING_STATUS:
        raise APIError(f"Invalid status. Allowed: {', '.join(BOOKING_STATUS)}", status_code=422)
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise APIError("Booking not found", status_code=404)

    # Provider on the booking advances it; the owning consumer may cancel.
    provider = _current_provider(db, user)
    is_provider = provider and provider.id == booking.provider_id
    owns_device = db.query(Device).filter(
        Device.id == booking.device_id, Device.owner_id == user.id
    ).first() is not None
    if not (is_provider or owns_device):
        raise APIError("You cannot modify this booking", status_code=403)

    booking.status = new_status
    EVENT = {
        "IN_PROGRESS": ("REPAIR_IN_PROGRESS", "Repair in progress"),
        "COMPLETED": ("REPAIR_COMPLETED", "Repair completed by provider"),
        "CANCELLED": ("BOOKING_CANCELLED", "Booking cancelled"),
    }.get(new_status)
    if EVENT:
        lifecycle_service.log_event(db, booking.device_id, EVENT[0], EVENT[1], user.name)
    # Notify the device owner of the status change.
    owner = db.query(Device).filter(Device.id == booking.device_id).first()
    if owner:
        notification_service.notify(db, owner.owner_id, "order", "Booking updated",
                                    f"Your booking is now {new_status.replace('_', ' ').lower()}.", commit=False)
    db.commit()
    db.refresh(booking)
    return BookingOut.model_validate(booking)
