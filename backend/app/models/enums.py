"""Allowed values for constrained columns (Phase 0 status lifecycles).

These are used with SQLAlchemy Enum(native_enum=False), which renders as a
VARCHAR + CHECK constraint — portable across PostgreSQL and SQLite while still
enforcing the allowed set at the database level (data integrity / NFR).
"""

ROLES = ("consumer", "provider", "refurbisher", "recycler", "supplier", "admin")

DEVICE_TYPES = ("smartphone", "laptop", "tablet")
WORKING_STATUS = ("working", "faulty", "not_working")
RECOMMENDATIONS = ("REPAIR", "REUSE", "RESALE", "REFURBISH", "RECYCLE")

PROVIDER_TYPES = ("technician", "refurbisher", "recycler", "supplier")

QUOTATION_STATUS = ("PENDING", "SENT", "ACCEPTED", "REJECTED", "EXPIRED")
BOOKING_STATUS = ("REQUESTED", "CONFIRMED", "IN_PROGRESS", "COMPLETED", "CANCELLED")
LISTING_STATUS = ("ACTIVE", "RESERVED", "SOLD", "REMOVED")
COLLECTION_STATUS = ("REQUESTED", "SCHEDULED", "PICKED_UP", "RECEIVED", "RECYCLED")

# --- Marketplace taxonomy (extended) ---
# A listing can be a whole device, an individual component, or a recovered
# material sold by quantity. "other" is allowed for any kind (a catch-all so
# sellers can list something not covered above).
LISTING_KINDS = ("device", "component", "material")

DEVICE_CATEGORIES = ("smartphone", "laptop", "tablet")
COMPONENT_CATEGORIES = ("cpu", "gpu", "ram", "motherboard", "storage", "cooler")
MATERIAL_CATEGORIES = ("rare_earth", "silicon", "copper", "aluminium", "gold")
OTHER_CATEGORY = ("other",)

LISTING_CATEGORIES = (
    DEVICE_CATEGORIES + COMPONENT_CATEGORIES + MATERIAL_CATEGORIES + OTHER_CATEGORY
)

# Units for material (quantity-based) listings.
MATERIAL_UNITS = ("g", "kg", "tonne", "piece")


def categories_for_kind(kind: str) -> tuple:
    """Valid categories for a given listing kind (+ 'other' catch-all)."""
    base = {
        "device": DEVICE_CATEGORIES,
        "component": COMPONENT_CATEGORIES,
        "material": MATERIAL_CATEGORIES,
    }.get(kind, ())
    return base + OTHER_CATEGORY
