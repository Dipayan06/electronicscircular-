"""Device endpoints (FR-B). All protected — the current user is resolved from the
JWT and scopes every operation to their own devices."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.device import DeviceCreate, DeviceUpdate
from ..schemas.assessment import AssessmentIn
from ..services import device_service
from ..utils.responses import success

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", summary="List my devices")
def list_devices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(device_service.list_devices(db, user), "Devices retrieved")


@router.post("", status_code=status.HTTP_201_CREATED, summary="Register a device")
def create_device(data: DeviceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(device_service.create_device(db, user, data), "Device registered successfully")


@router.get("/{device_id}", summary="Get one of my devices")
def get_device(device_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(device_service.get_device(db, user, device_id), "Device retrieved")


@router.put("/{device_id}", summary="Update one of my devices")
def update_device(device_id: int, data: DeviceUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(device_service.update_device(db, user, device_id, data), "Device updated")


@router.delete("/{device_id}", summary="Delete one of my devices")
def delete_device(device_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    device_service.delete_device(db, user, device_id)
    return success(None, "Device deleted")


# --- Assessment + recommendation (FR-C, FR-D) ---

@router.post("/{device_id}/assessment", summary="Assess condition → get recommendation")
def assess_device(device_id: int, data: AssessmentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    result = device_service.assess_device(db, user, device_id, data)
    return success(result, "Assessment saved and recommendation generated")


@router.get("/{device_id}/recommendation", summary="Get the current recommendation")
def get_recommendation(device_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(device_service.get_recommendation(db, user, device_id), "Recommendation retrieved")


# --- Digital Device Passport (FR-J) ---

@router.get("/{device_id}/lifecycle", summary="Get the device's full lifecycle timeline")
def get_lifecycle(device_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(device_service.get_device_lifecycle(db, user, device_id), "Lifecycle retrieved")
