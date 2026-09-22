"""Dashboard aggregation (FR-K). Computes the current user's counts + recent
activity from the real database across all domains."""
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Device, Quotation, Booking, ResaleListing, CollectionRequest, LifecycleEvent, User


def _rel_time(ts: datetime) -> str:
    diff = datetime.utcnow() - ts
    hours = int(diff.total_seconds() // 3600)
    if hours < 1:
        return "just now"
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def get_dashboard(db: Session, user: User) -> dict:
    devices = db.query(Device).filter(Device.owner_id == user.id).all()
    device_ids = [d.id for d in devices]

    quotes = db.query(Quotation).filter(Quotation.device_id.in_(device_ids)).all() if device_ids else []
    bookings = db.query(Booking).filter(Booking.device_id.in_(device_ids)).all() if device_ids else []
    listings = db.query(ResaleListing).filter(ResaleListing.seller_id == user.id).all()
    collections = db.query(CollectionRequest).filter(CollectionRequest.device_id.in_(device_ids)).all() if device_ids else []

    active_bookings = [b for b in bookings if b.status in ("CONFIRMED", "IN_PROGRESS")]
    stats = {
        "devices": len(devices),
        "activeRequests": len([q for q in quotes if q.status in ("PENDING", "SENT")]) + len(active_bookings),
        "pendingQuotes": len([q for q in quotes if q.status == "SENT"]),
        "upcomingBookings": len(active_bookings),
        "listings": len([l for l in listings if l.status == "ACTIVE"]),
        "collections": len(collections),
    }

    events = (
        db.query(LifecycleEvent)
        .filter(LifecycleEvent.device_id.in_(device_ids))
        .order_by(LifecycleEvent.timestamp.desc())
        .limit(6)
        .all()
    ) if device_ids else []
    activity = [{"text": e.description, "time": _rel_time(e.timestamp)} for e in events]

    return {"stats": stats, "activity": activity}
