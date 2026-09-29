"""Circular assistant endpoints — the in-house small language model.
Status is public; everything else needs a login."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.assistant import ChatIn, DeviceRefIn, ParseIn
from ..services import assistant_service
from ..utils.responses import success

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.get("/status", summary="Is the assistant model loaded? (size and shape)")
def status():
    return success(assistant_service.status(), "Assistant status")


@router.post("/chat", summary="Ask the help assistant a question")
def chat(data: ChatIn, user: User = Depends(get_current_user)):
    return success(assistant_service.chat(data.message), "Reply generated")


@router.post("/parse-assessment", summary="Turn a free-text fault description into assessment values")
def parse_assessment(data: ParseIn, user: User = Depends(get_current_user)):
    return success(assistant_service.parse_description(data.text), "Description parsed")


@router.post("/explain", summary="Explain a device's current recommendation in plain language")
def explain(data: DeviceRefIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(assistant_service.explain(db, user, data.device_id), "Explanation generated")


@router.post("/listing-draft", summary="Draft a listing title and description for one of my devices")
def listing_draft(data: DeviceRefIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(assistant_service.listing_draft(db, user, data.device_id), "Listing draft generated")
