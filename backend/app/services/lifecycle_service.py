"""Lifecycle service (FR-J). The single writer/reader of the device timeline —
every mutating service calls log_event, mirroring Phase 1 §1.3."""
from sqlalchemy.orm import Session

from ..models import LifecycleEvent


def log_event(db: Session, device_id: int, type: str, description: str, actor: str = "System"):
    event = LifecycleEvent(device_id=device_id, type=type, description=description, actor=actor)
    db.add(event)
    # Caller commits (keeps the event in the same transaction as the mutation).
    return event


def get_lifecycle(db: Session, device_id: int) -> list[LifecycleEvent]:
    return (
        db.query(LifecycleEvent)
        .filter(LifecycleEvent.device_id == device_id)
        .order_by(LifecycleEvent.timestamp.asc())
        .all()
    )
