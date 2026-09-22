"""Device business logic (FR-B). Every function is scoped to the acting user —
a device is only ever visible to its owner (Phase 0 §5 persistence rule: never
trust a client-supplied user id)."""
from sqlalchemy.orm import Session

from datetime import datetime

from ..models import Device, DeviceAssessment, User
from ..schemas.device import DeviceCreate, DeviceUpdate, DeviceOut
from ..schemas.assessment import AssessmentIn
from ..schemas.lifecycle import LifecycleEventOut
from ..utils.responses import APIError
from . import lifecycle_service
from .recommendation import recommend


def _owned_device(db: Session, user: User, device_id: int) -> Device:
    """Fetch a device the user owns, or 404 (don't reveal others' devices exist)."""
    device = (
        db.query(Device)
        .filter(Device.id == device_id, Device.owner_id == user.id)
        .first()
    )
    if not device:
        raise APIError("Device not found", status_code=404)
    return device


def list_devices(db: Session, user: User) -> list[DeviceOut]:
    devices = (
        db.query(Device)
        .filter(Device.owner_id == user.id)
        .order_by(Device.created_at.desc())
        .all()
    )
    return [DeviceOut.model_validate(d) for d in devices]


def get_device(db: Session, user: User, device_id: int) -> DeviceOut:
    return DeviceOut.model_validate(_owned_device(db, user, device_id))


def create_device(db: Session, user: User, data: DeviceCreate) -> DeviceOut:
    device = Device(owner_id=user.id, **data.model_dump())
    db.add(device)
    db.flush()  # assign device.id before logging
    lifecycle_service.log_event(db, device.id, "DEVICE_REGISTERED",
                                "Device registered on the platform", user.name)
    db.commit()
    db.refresh(device)
    return DeviceOut.model_validate(device)


def update_device(db: Session, user: User, device_id: int, data: DeviceUpdate) -> DeviceOut:
    device = _owned_device(db, user, device_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return DeviceOut.model_validate(device)


def delete_device(db: Session, user: User, device_id: int) -> None:
    device = _owned_device(db, user, device_id)
    db.delete(device)  # cascades to assessments + lifecycle events
    db.commit()


# --- Assessment + recommendation (FR-C, FR-D) ---

def assess_device(db: Session, user: User, device_id: int, data: AssessmentIn) -> dict:
    """Store an assessment, compute the recommendation via the rule engine, persist
    it on the device, and log a CONDITION_ASSESSED lifecycle event."""
    device = _owned_device(db, user, device_id)

    age_years = (datetime.utcnow().year - device.purchase_year) if device.purchase_year else 0
    rec = recommend({**data.model_dump(), "age_years": age_years})

    assessment = DeviceAssessment(device_id=device.id, **data.model_dump())
    db.add(assessment)
    device.recommendation = rec["action"]
    lifecycle_service.log_event(db, device.id, "CONDITION_ASSESSED",
                                f"Condition assessed → recommendation: {rec['action']}", user.name)
    db.commit()
    return {"recommendation": rec}


def get_recommendation(db: Session, user: User, device_id: int) -> dict:
    """Return the current recommendation, recomputed from the latest assessment."""
    device = _owned_device(db, user, device_id)
    assessment = (
        db.query(DeviceAssessment)
        .filter(DeviceAssessment.device_id == device.id)
        .order_by(DeviceAssessment.created_at.desc())
        .first()
    )
    if not assessment:
        raise APIError("This device has not been assessed yet", status_code=404)

    age_years = (datetime.utcnow().year - device.purchase_year) if device.purchase_year else 0
    rec = recommend({
        "screen": assessment.screen, "battery": assessment.battery, "body": assessment.body,
        "powers_on": assessment.powers_on, "charging": assessment.charging,
        "water_damage": assessment.water_damage, "age_years": age_years,
    })
    return {"recommendation": rec}


# --- Digital Device Passport (FR-J) ---

def get_device_lifecycle(db: Session, user: User, device_id: int) -> list[LifecycleEventOut]:
    """Return the full, ordered event timeline for a device the user owns."""
    _owned_device(db, user, device_id)  # 404 if not the owner
    events = lifecycle_service.get_lifecycle(db, device_id)
    return [LifecycleEventOut.model_validate(e) for e in events]
