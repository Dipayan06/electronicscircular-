"""Notification endpoints (Feature 3). All protected + user-scoped (a user only
ever sees or mutates their own notifications — prevents IDOR/BOLA)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.notification import NotificationOut
from ..services import notification_service
from ..utils.responses import success

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", summary="List my notifications + unread count")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = notification_service.list_for_user(db, user)
    data = {
        "items": [NotificationOut.model_validate(n) for n in items],
        "unread": notification_service.unread_count(db, user),
    }
    return success(data, "Notifications retrieved")


@router.get("/unread-count", summary="My unread notification count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success({"unread": notification_service.unread_count(db, user)}, "Unread count")


@router.put("/{notification_id}/read", summary="Mark one notification read")
def mark_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(NotificationOut.model_validate(notification_service.mark_read(db, user, notification_id)), "Marked read")


@router.put("/read-all", summary="Mark all my notifications read")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = notification_service.mark_all_read(db, user)
    return success({"marked": n}, "All notifications marked read")
