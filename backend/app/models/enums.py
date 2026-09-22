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
