"""Dashboard endpoint (FR-K)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..services import dashboard_service
from ..utils.responses import success

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", summary="Dashboard stats + recent activity for the current user")
def get_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(dashboard_service.get_dashboard(db, user), "Dashboard retrieved")
