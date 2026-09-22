"""Collection & recycling business logic (FR-I). Drives a device through the
end-of-life status lifecycle, logging an event at each stage — the events that
close the circular loop on the Digital Device Passport."""
from sqlalchemy.orm import Session

from ..models import CollectionRequest, Device, Provider, User
from ..schemas.collection import CollectionCreate, CollectionOut
from ..models.enums import COLLECTION_STATUS
from ..utils.responses import APIError
from . import lifecycle_service

PROVIDER_ROLES = ("provider", "refurbisher", "recycler", "supplier")

# Lifecycle event emitted when a collection reaches each status.
STATUS_EVENT = {
    "SCHEDULED": ("COLLECTION_SCHEDULED", "Pickup scheduled"),
    "PICKED_UP": ("PICKED_UP", "Device picked up by collector"),
    "RECEIVED": ("RECEIVED", "Device received at recycling facility"),
    "RECYCLED": ("RECYCLED", "Device responsibly recycled — lifecycle closed"),
}


def _current_provider(db: Session, user: User) -> Provider | None:
    return db.query(Provider).filter(Provider.user_id == user.id).first()


def list_collections(db: Session, user: User) -> list[CollectionOut]:
    query = db.query(CollectionRequest)
    provider = _current_provider(db, user)
    if user.role.name in PROVIDER_ROLES and provider:
        query = query.filter(CollectionRequest.collector_id == provider.id)
    else:
        device_ids = [d.id for d in db.query(Device).filter(Device.owner_id == user.id).all()]
        if not device_ids:
            return []
        query = query.filter(CollectionRequest.device_id.in_(device_ids))
    rows = query.order_by(CollectionRequest.created_at.desc()).all()
    return [CollectionOut.model_validate(r) for r in rows]


def request_collection(db: Session, user: User, data: CollectionCreate) -> CollectionOut:
    device = db.query(Device).filter(
        Device.id == data.device_id, Device.owner_id == user.id
    ).first()
    if not device:
        raise APIError("Device not found", status_code=404)
    collector = db.query(Provider).filter(Provider.id == data.collector_id).first()
    if not collector:
        raise APIError("Collector not found", status_code=404)

    req = CollectionRequest(
        device_id=device.id, collector_id=collector.id,
        address=data.address, preferred_date=data.preferred_date, status="REQUESTED",
    )
    db.add(req)
    db.flush()
    lifecycle_service.log_event(db, device.id, "COLLECTION_REQUESTED",
                                f"Collection requested from {collector.name}", user.name)
    db.commit()
    db.refresh(req)
    return CollectionOut.model_validate(req)


def advance_collection(db: Session, user: User, collection_id: int, new_status: str) -> CollectionOut:
    if new_status not in COLLECTION_STATUS:
        raise APIError(f"Invalid status. Allowed: {', '.join(COLLECTION_STATUS)}", status_code=422)
    req = db.query(CollectionRequest).filter(CollectionRequest.id == collection_id).first()
    if not req:
        raise APIError("Collection request not found", status_code=404)

    # The collector on the request advances it; the owning consumer may also act.
    provider = _current_provider(db, user)
    is_collector = provider and provider.id == req.collector_id
    owns_device = db.query(Device).filter(
        Device.id == req.device_id, Device.owner_id == user.id
    ).first() is not None
    if not (is_collector or owns_device):
        raise APIError("You cannot modify this collection request", status_code=403)

    # Only allow moving forward along the defined flow.
    if COLLECTION_STATUS.index(new_status) <= COLLECTION_STATUS.index(req.status):
        raise APIError(f"Cannot move from {req.status} to {new_status}", status_code=400)

    req.status = new_status
    event = STATUS_EVENT.get(new_status)
    if event:
        lifecycle_service.log_event(db, req.device_id, event[0], event[1], user.name)
    db.commit()
    db.refresh(req)
    return CollectionOut.model_validate(req)
