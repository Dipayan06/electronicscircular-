"""Notification business logic (Feature 3). One writer used across the app so any
event can create a persistent, per-user notification."""
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Notification, User


def notify(db: Session, user_id: int, type: str, title: str, message: str, meta: dict | None = None,
           commit: bool = True) -> Notification:
    """Create a notification for a user. Callers already inside a transaction can
    pass commit=False to include it in their own commit."""
    n = Notification(user_id=user_id, type=type, title=title, message=message, meta=meta)
    db.add(n)
    if commit:
        db.commit()
        db.refresh(n)
    return n


def list_for_user(db: Session, user: User) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


def unread_count(db: Session, user: User) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.read == False)  # noqa: E712
        .count()
    )


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    n = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not n:
        from ..utils.responses import APIError
        raise APIError("Notification not found", status_code=404)
    if not n.read:
        n.read = True
        n.read_at = datetime.utcnow()
        db.commit()
        db.refresh(n)
    return n


def mark_all_read(db: Session, user: User) -> int:
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.read == False)  # noqa: E712
        .all()
    )
    now = datetime.utcnow()
    for n in rows:
        n.read = True
        n.read_at = now
    db.commit()
    return len(rows)
