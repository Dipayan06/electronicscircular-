"""Resale-estimate endpoints. The estimate needs a login (it can read the
caller's own device assessment); category references are public to read and
admin-only to change."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user, require_role
from ..models import User
from ..schemas.valuation import EstimateIn, CategoryPriceUpdateIn
from ..services import valuation_service
from ..utils.responses import success

router = APIRouter(prefix="/valuation", tags=["Valuation"])


@router.post("/estimate", summary="Estimate the resale value of a device or component")
def estimate(data: EstimateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    result = valuation_service.estimate(
        db, user, data.kind, data.type, purchase_price=data.purchase_price,
        purchase_year=data.purchase_year, condition=data.condition, device_id=data.device_id)
    return success(result, "Estimate calculated")


@router.get("/categories", summary="Typical new prices + depreciation per category")
def list_categories(db: Session = Depends(get_db)):
    return success(valuation_service.list_categories(db), "Category references retrieved")


@router.put("/categories/{category}", summary="Update a category reference (admin only)")
def update_category(category: str, data: CategoryPriceUpdateIn, db: Session = Depends(get_db),
                    admin: User = Depends(require_role("admin"))):
    return success(valuation_service.update_category(db, admin, category, data), "Category reference updated")
