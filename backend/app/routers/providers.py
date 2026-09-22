"""Provider endpoints (FR-E). Thin HTTP layer — delegates to the service layer.

These are public reads (a consumer browses providers before/without auth is fine
for the prototype). Mutating/admin endpoints (verify) arrive with auth in Phase 10.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import require_role
from ..models import User
from ..services import provider_service
from ..utils.responses import success

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("", summary="List providers (optional ?type= filter)")
def list_providers(type: str | None = Query(default=None), db: Session = Depends(get_db)):
    data = provider_service.list_providers(db, type)
    return success(data, "Providers retrieved")


@router.get("/{provider_id}", summary="Get one provider")
def get_provider(provider_id: int, db: Session = Depends(get_db)):
    data = provider_service.get_provider(db, provider_id)
    return success(data, "Provider retrieved")


@router.put("/{provider_id}/verify", summary="Verify a provider (admin only)")
def verify_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    data = provider_service.verify_provider(db, provider_id)
    return success(data, "Provider verified")
