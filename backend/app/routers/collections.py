"""Collection & recycling endpoints (FR-I). All protected."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.collection import CollectionCreate, CollectionStatusUpdate
from ..services import collection_service
from ..utils.responses import success

router = APIRouter(prefix="/collections", tags=["Collection & Recycling"])


@router.get("", summary="List my collection requests / assigned pickups")
def list_collections(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(collection_service.list_collections(db, user), "Collections retrieved")


@router.post("", status_code=status.HTTP_201_CREATED, summary="Request a collection")
def request_collection(data: CollectionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(collection_service.request_collection(db, user, data), "Collection requested")


@router.put("/{collection_id}/status", summary="Advance collection status (collector)")
def advance_status(collection_id: int, data: CollectionStatusUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(collection_service.advance_collection(db, user, collection_id, data.status), "Collection updated")
