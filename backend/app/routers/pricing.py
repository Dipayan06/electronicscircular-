"""Material reference pricing endpoints (Feature 2) + price check (Feature 4).
Reads are public (prices are shown on the marketplace); writes are admin-only."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user, require_role
from ..models import User
from ..schemas.pricing import PriceUpdateIn, PriceCheckIn
from ..services import pricing_service
from ..utils.responses import success

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.get("/materials", summary="Reference prices for all materials (with source + freshness)")
def list_prices(db: Session = Depends(get_db)):
    data = {"items": pricing_service.list_prices(db), "feed_configured": pricing_service.feed_configured()}
    return success(data, "Reference prices retrieved")


@router.get("/materials/{material}", summary="Reference price for one material")
def get_price(material: str, db: Session = Depends(get_db)):
    return success(pricing_service.get_price(db, material), "Reference price retrieved")


@router.get("/materials/{material}/history", summary="Change history of a material's reference price")
def price_history(material: str, db: Session = Depends(get_db)):
    return success(pricing_service.history(db, material), "Price history retrieved")


@router.put("/materials/{material}", summary="Set a reference price / regulation band (admin only)")
def set_price(material: str, data: PriceUpdateIn, db: Session = Depends(get_db),
              admin: User = Depends(require_role("admin"))):
    return success(pricing_service.set_reference(db, admin, material, data), "Reference price updated")


@router.post("/refresh", summary="Pull prices from the configured market feed (admin only)")
def refresh(db: Session = Depends(get_db), admin: User = Depends(require_role("admin"))):
    return success(pricing_service.refresh_from_feed(db, admin), "Feed refresh finished")


@router.post("/check", summary="Preview how a listing price will be classified")
def check_price(data: PriceCheckIn, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return success(pricing_service.assess_price(db, data.kind, data.type, data.unit, data.price), "Price checked")
