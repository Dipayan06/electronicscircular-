"""Model package. Importing every model here ensures they are all registered on
Base.metadata (so create_all / migrations see the full schema)."""
from .user import Role, User
from .device import Device, DeviceAssessment
from .provider import Provider, ProviderService, SparePart
from .quotation import Quotation
from .booking import Booking
from .listing import ResaleListing
from .collection import CollectionRequest
from .lifecycle import LifecycleEvent
from .notification import Notification

__all__ = [
    "Role", "User", "Device", "DeviceAssessment", "Provider", "ProviderService",
    "SparePart", "Quotation", "Booking", "ResaleListing", "CollectionRequest",
    "LifecycleEvent", "Notification",
]
