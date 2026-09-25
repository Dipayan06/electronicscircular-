"""Notification schemas (Feature 3)."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    message: str
    read: bool
    read_at: datetime | None = None
    meta: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
