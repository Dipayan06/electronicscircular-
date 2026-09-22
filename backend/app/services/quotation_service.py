"""Quotation business logic (FR-F). Implements the request → quote → accept/reject
workflow, scoped correctly for consumers vs providers."""
from sqlalchemy.orm import Session

from ..models import Quotation, Device, Provider, User
from ..schemas.quotation import QuotationCreate, QuoteSubmit, QuotationOut
from ..utils.responses import APIError
from . import lifecycle_service

PROVIDER_ROLES = ("provider", "refurbisher", "recycler", "supplier")


def _current_provider(db: Session, user: User) -> Provider | None:
    return db.query(Provider).filter(Provider.user_id == user.id).first()


def list_quotations(db: Session, user: User) -> list[QuotationOut]:
    query = db.query(Quotation)
    provider = _current_provider(db, user)
    if user.role.name in PROVIDER_ROLES and provider:
        # Provider sees requests directed to them.
        query = query.filter(Quotation.provider_id == provider.id)
    else:
        # Consumer sees quotes on their own devices.
        device_ids = [d.id for d in db.query(Device).filter(Device.owner_id == user.id).all()]
        if not device_ids:
            return []
        query = query.filter(Quotation.device_id.in_(device_ids))
    quotes = query.order_by(Quotation.created_at.desc()).all()
    return [QuotationOut.model_validate(q) for q in quotes]


def request_quotation(db: Session, user: User, data: QuotationCreate) -> QuotationOut:
    # Consumer must own the device.
    device = db.query(Device).filter(
        Device.id == data.device_id, Device.owner_id == user.id
    ).first()
    if not device:
        raise APIError("Device not found", status_code=404)
    provider = db.query(Provider).filter(Provider.id == data.provider_id).first()
    if not provider:
        raise APIError("Provider not found", status_code=404)

    quote = Quotation(device_id=device.id, provider_id=provider.id,
                      problem=data.problem, status="PENDING")
    db.add(quote)
    db.flush()
    lifecycle_service.log_event(db, device.id, "QUOTE_REQUESTED",
                                f"Quotation requested from {provider.name}", user.name)
    db.commit()
    db.refresh(quote)
    return QuotationOut.model_validate(quote)


def submit_quote(db: Session, user: User, quote_id: int, data: QuoteSubmit) -> QuotationOut:
    """Provider action: fill in the estimate (PENDING → SENT)."""
    quote = db.query(Quotation).filter(Quotation.id == quote_id).first()
    if not quote:
        raise APIError("Quotation not found", status_code=404)
    provider = _current_provider(db, user)
    if not provider or provider.id != quote.provider_id:
        raise APIError("This quotation was not directed to you", status_code=403)
    if quote.status not in ("PENDING", "SENT"):
        raise APIError(f"Cannot quote a {quote.status.lower()} request", status_code=400)

    quote.cost = data.cost
    quote.days = data.days
    quote.description = data.description
    quote.status = "SENT"
    db.commit()
    db.refresh(quote)
    return QuotationOut.model_validate(quote)


def respond_to_quote(db: Session, user: User, quote_id: int, accept: bool) -> QuotationOut:
    """Consumer accepts/rejects a sent quote (SENT → ACCEPTED | REJECTED)."""
    quote = db.query(Quotation).filter(Quotation.id == quote_id).first()
    if not quote:
        raise APIError("Quotation not found", status_code=404)
    device = db.query(Device).filter(
        Device.id == quote.device_id, Device.owner_id == user.id
    ).first()
    if not device:
        raise APIError("Quotation not found", status_code=404)
    if quote.status != "SENT":
        raise APIError("Only a sent quotation can be accepted or rejected", status_code=400)

    quote.status = "ACCEPTED" if accept else "REJECTED"
    if accept:
        lifecycle_service.log_event(db, device.id, "QUOTE_ACCEPTED",
                                    f"Quotation accepted (₹{int(quote.cost or 0):,})", user.name)
    db.commit()
    db.refresh(quote)
    return QuotationOut.model_validate(quote)
