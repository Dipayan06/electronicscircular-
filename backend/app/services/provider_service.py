"""Provider business logic (Phase 1 §1.2 service layer). Routers call these;
they own the queries and rules and never touch HTTP."""
from sqlalchemy.orm import Session

from ..models import Provider
from ..schemas.provider import ProviderOut
from ..utils.responses import APIError


def list_providers(db: Session, type_filter: str | None = None) -> list[ProviderOut]:
    query = db.query(Provider)
    if type_filter and type_filter != "all":
        query = query.filter(Provider.type == type_filter)
    providers = query.order_by(Provider.name).all()
    return [ProviderOut.from_orm_provider(p) for p in providers]


def get_provider(db: Session, provider_id: int) -> ProviderOut:
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise APIError("Provider not found", status_code=404)
    return ProviderOut.from_orm_provider(provider)


def verify_provider(db: Session, provider_id: int) -> ProviderOut:
    """Admin action (FR-K3): mark a provider as verified."""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise APIError("Provider not found", status_code=404)
    provider.verified = True
    db.commit()
    db.refresh(provider)
    return ProviderOut.from_orm_provider(provider)
