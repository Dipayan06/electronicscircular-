"""Pydantic schemas for providers (Phase 1 §1.2 API-layer validation)."""
from pydantic import BaseModel, ConfigDict


class ProviderOut(BaseModel):
    id: int
    name: str
    type: str
    location: str | None = None
    verified: bool
    rating: float
    contact: str | None = None
    services: list[str] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_provider(cls, p) -> "ProviderOut":
        """Map an ORM Provider (with service_items relationship) to the schema."""
        return cls(
            id=p.id, name=p.name, type=p.type, location=p.location,
            verified=p.verified, rating=p.rating, contact=p.contact,
            services=[s.name for s in p.service_items],
        )
