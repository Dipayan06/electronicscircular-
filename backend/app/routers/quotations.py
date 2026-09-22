"""Quotation endpoints (FR-F). All protected; scoped by role in the service."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.quotation import QuotationCreate, QuoteSubmit
from ..services import quotation_service
from ..utils.responses import success

router = APIRouter(prefix="/quotations", tags=["Quotations"])


@router.get("", summary="List my quotations (consumer) / incoming (provider)")
def list_quotations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(quotation_service.list_quotations(db, user), "Quotations retrieved")


@router.post("", status_code=status.HTTP_201_CREATED, summary="Request a quotation")
def request_quotation(data: QuotationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(quotation_service.request_quotation(db, user, data), "Quotation requested")


@router.put("/{quote_id}/quote", summary="Submit a quote (provider)")
def submit_quote(quote_id: int, data: QuoteSubmit, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(quotation_service.submit_quote(db, user, quote_id, data), "Quote submitted")


@router.put("/{quote_id}/accept", summary="Accept a quotation")
def accept_quote(quote_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(quotation_service.respond_to_quote(db, user, quote_id, True), "Quotation accepted")


@router.put("/{quote_id}/reject", summary="Reject a quotation")
def reject_quote(quote_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(quotation_service.respond_to_quote(db, user, quote_id, False), "Quotation rejected")
