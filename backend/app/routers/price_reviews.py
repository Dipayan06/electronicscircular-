"""Price-review endpoints (Feature 4). Admins list and decide reviews; sellers
can see only the reviews on their own listings."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user, require_role
from ..models import User
from ..schemas.pricing import ReviewDecisionIn
from ..services import price_review_service
from ..utils.responses import success

router = APIRouter(prefix="/price-reviews", tags=["Price regulation"])


@router.get("", summary="List price reviews (admin only; optional ?status=PENDING)")
def list_reviews(status: str | None = Query(default=None), db: Session = Depends(get_db),
                 _admin: User = Depends(require_role("admin"))):
    return success(price_review_service.list_reviews(db, status), "Price reviews retrieved")


@router.get("/mine", summary="Price reviews on my listings")
def my_reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(price_review_service.list_for_seller(db, user), "Your price reviews")


@router.put("/{review_id}/approve", summary="Approve a flagged price (admin only)")
def approve(review_id: int, data: ReviewDecisionIn | None = None, db: Session = Depends(get_db),
            admin: User = Depends(require_role("admin"))):
    note = data.note if data else None
    return success(price_review_service.decide(db, admin, review_id, True, note), "Price approved")


@router.put("/{review_id}/reject", summary="Reject a flagged price (admin only)")
def reject(review_id: int, data: ReviewDecisionIn | None = None, db: Session = Depends(get_db),
           admin: User = Depends(require_role("admin"))):
    note = data.note if data else None
    return success(price_review_service.decide(db, admin, review_id, False, note), "Price rejected")
