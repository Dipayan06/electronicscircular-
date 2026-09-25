"""Price-review workflow (Feature 4). Admins approve or reject listings whose
price fell outside the normal band. Every decision is kept on the PriceReview
row (who, when, note), which forms the audit trail."""
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import PriceReview, ResaleListing, User, Role
from ..utils.responses import APIError
from . import notification_service


def serialize(r: PriceReview) -> dict:
    l = r.listing
    return {
        "id": r.id,
        "listing_id": r.listing_id,
        "listing_title": l.title if l else None,
        "listing_status": l.status if l else None,
        "seller_id": r.seller_id,
        "seller": r.seller.name if r.seller else None,
        "material": r.material,
        "level": r.level,
        "listed_price": float(r.listed_price),
        "listed_unit": r.listed_unit,
        "reference_price": float(r.reference_price) if r.reference_price is not None else None,
        "reference_unit": r.reference_unit,
        "ratio": float(r.ratio) if r.ratio is not None else None,
        "reason": r.reason,
        "justification": r.justification,
        "status": r.status,
        "reviewer": r.reviewer.name if r.reviewer else None,
        "reviewer_note": r.reviewer_note,
        "created_at": r.created_at,
        "decided_at": r.decided_at,
    }


def open_review(db: Session, listing: ResaleListing, assessment: dict, justification: str | None) -> PriceReview:
    """Create the review row for a newly flagged listing and alert admins.
    Runs inside the caller's transaction (no commit here)."""
    ref = assessment.get("reference") or {}
    review = PriceReview(
        listing_id=listing.id, seller_id=listing.seller_id, material=listing.type,
        level=assessment["level"], listed_price=listing.price, listed_unit=listing.unit,
        reference_price=ref.get("reference_price"), reference_unit=ref.get("unit"),
        ratio=assessment.get("ratio"), reason=assessment["reason"][:300],
        justification=(justification or "").strip()[:600] or None,
    )
    db.add(review)
    detail = (f"{assessment['ratio']:g}× the reference price" if assessment.get("ratio") is not None
              else "a unit that can't be compared to the reference")
    admins = db.query(User).join(Role).filter(Role.name == "admin").all()
    for a in admins:
        notification_service.notify(
            db, a.id, "price", f"Price review needed ({assessment['level']})",
            f"“{listing.title}” by {listing.seller.name if listing.seller else 'a seller'} is listed at {detail}.",
            meta={"listing_id": listing.id}, commit=False)
    return review


def list_reviews(db: Session, status: str | None = None) -> list[dict]:
    q = db.query(PriceReview)
    if status:
        q = q.filter(PriceReview.status == status.upper())
    return [serialize(r) for r in q.order_by(PriceReview.created_at.desc()).all()]


def list_for_seller(db: Session, seller: User) -> list[dict]:
    rows = (db.query(PriceReview).filter(PriceReview.seller_id == seller.id)
            .order_by(PriceReview.created_at.desc()).all())
    return [serialize(r) for r in rows]


def decide(db: Session, admin: User, review_id: int, approve: bool, note: str | None) -> dict:
    review = db.query(PriceReview).filter(PriceReview.id == review_id).first()
    if not review:
        raise APIError("Review not found", status_code=404)
    if review.status != "PENDING":
        raise APIError(f"This review was already {review.status.lower()}", status_code=409)

    listing = review.listing
    review.status = "APPROVED" if approve else "REJECTED"
    review.reviewer_id = admin.id
    review.reviewer_note = (note or "").strip()[:400] or None
    review.decided_at = datetime.utcnow()
    # Only move the listing if it is still waiting on this review.
    if listing and listing.status in ("PRICE_REVIEW_REQUIRED", "SUSPENDED_PENDING_REVIEW"):
        listing.status = "ACTIVE" if approve else "REJECTED"

    verdict = "approved — it is now live" if approve else "rejected"
    msg = f"Your price for “{listing.title if listing else 'a listing'}” was {verdict}."
    if review.reviewer_note:
        msg += f" Note: {review.reviewer_note}"
    notification_service.notify(db, review.seller_id, "price",
                                "Price approved" if approve else "Price rejected", msg,
                                meta={"listing_id": review.listing_id}, commit=False)
    db.commit()
    db.refresh(review)
    return serialize(review)
