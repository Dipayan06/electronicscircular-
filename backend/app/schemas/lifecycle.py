"""Lifecycle event schema (FR-J) — one entry of the Digital Device Passport."""
import datetime

from pydantic import BaseModel, ConfigDict


class LifecycleEventOut(BaseModel):
    id: int
    device_id: int
    type: str
    description: str
    actor: str | None = None
    timestamp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
