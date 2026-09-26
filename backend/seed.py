"""Database seed script (Phase 5 §28).

Creates all tables and inserts deterministic demo data so the prototype can be
demonstrated immediately: demo accounts, providers, devices, an assessment, a
quotation, marketplace listings, and lifecycle events.

Run from the backend/ directory:
    python seed.py

Demo accounts (development passwords — change for any real deployment):
    consumer : demo.user@example.com     / password123
    provider : demo.provider@example.com / password123
    admin    : admin@example.com         / password123
"""
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.database import Base, engine, SessionLocal
from app import models
from app.models import (
    Role, User, Device, DeviceAssessment, Provider, ProviderService, SparePart,
    Quotation, ResaleListing, LifecycleEvent, Notification,
    MaterialPrice, MaterialPriceHistory, PriceReview, CategoryPrice,
)
from app.models.enums import ROLES
from app.utils.security import hash_password

DEV_PASSWORD = "password123"


def reset_schema():
    """Drop and recreate all tables (clean slate for the demo)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed():
    reset_schema()
    db = SessionLocal()
    try:
        # --- Roles ---
        roles = {name: Role(name=name) for name in ROLES}
        db.add_all(roles.values())
        db.flush()

        # --- Users --- (seeded demo accounts are pre-verified so existing flows work;
        # the @gmail.com/@yahoo.com domain rule applies to NEW self-registrations)
        consumer = User(name="Priya Sharma", email="demo.user@example.com", is_verified=True,
                        password_hash=hash_password(DEV_PASSWORD), role_id=roles["consumer"].id)
        provider_user = User(name="FixIt Labs", email="demo.provider@example.com", is_verified=True,
                             password_hash=hash_password(DEV_PASSWORD), role_id=roles["provider"].id)
        admin = User(name="Site Admin", email="admin@example.com", is_verified=True,
                     password_hash=hash_password(DEV_PASSWORD), role_id=roles["admin"].id)
        db.add_all([consumer, provider_user, admin])
        db.flush()

        # --- Providers (FR-E) ---
        p_fixit = Provider(user_id=provider_user.id, name="FixIt Labs", type="technician",
                           location="Bengaluru", verified=True, rating=4.6, contact="fixit@example.com")
        p_mobmed = Provider(name="MobileMedic", type="technician", location="Mumbai",
                            verified=True, rating=4.3, contact="care@example.com")
        p_quick = Provider(name="QuickMob", type="technician", location="Delhi",
                           verified=False, rating=3.9, contact="hello@example.com")
        p_renew = Provider(name="ReNew Refurb", type="refurbisher", location="Pune",
                           verified=True, rating=4.7, contact="renew@example.com")
        p_green = Provider(name="GreenCycle", type="recycler", location="Pune",
                           verified=True, rating=4.5, contact="pickup@example.com")
        p_parts = Provider(name="PartsHub", type="supplier", location="Chennai",
                           verified=True, rating=4.2, contact="sales@example.com")
        providers = [p_fixit, p_mobmed, p_quick, p_renew, p_green, p_parts]
        db.add_all(providers)
        db.flush()

        # provider services (1:N)
        db.add_all([
            ProviderService(provider_id=p_fixit.id, name="Screen repair"),
            ProviderService(provider_id=p_fixit.id, name="Battery replacement"),
            ProviderService(provider_id=p_fixit.id, name="Board-level repair"),
            ProviderService(provider_id=p_green.id, name="Doorstep collection"),
            ProviderService(provider_id=p_green.id, name="Certified recycling"),
        ])
        # spare parts (FR-L)
        db.add_all([
            SparePart(supplier_id=p_parts.id, name="iPhone 12 screen", device_type="smartphone", price=4500, stock=12),
            SparePart(supplier_id=p_parts.id, name="XPS 13 battery", device_type="laptop", price=3800, stock=7),
        ])

        # --- Devices (FR-B) ---
        d_xps = Device(owner_id=consumer.id, type="laptop", brand="Dell", model="XPS 13",
                       serial="DXPS-9921", purchase_year=2021, working_status="working",
                       accessories="Charger", recommendation="REPAIR")
        d_ip12 = Device(owner_id=consumer.id, type="smartphone", brand="Apple", model="iPhone 12",
                        serial="IMEI-35771", purchase_year=2022, working_status="faulty",
                        accessories="Charger, Case", recommendation="RESALE")
        d_tab = Device(owner_id=consumer.id, type="tablet", brand="Samsung", model="Galaxy Tab A",
                       serial="STAB-1180", purchase_year=2018, working_status="not_working")
        db.add_all([d_xps, d_ip12, d_tab])
        db.flush()

        # --- Assessment (FR-C) ---
        db.add(DeviceAssessment(device_id=d_xps.id, screen="minor", battery="weak", body="good",
                                powers_on=True, charging=True, water_damage=False,
                                problems="Keyboard key sticks"))

        # --- Quotation (FR-F) ---
        db.add(Quotation(device_id=d_xps.id, provider_id=p_fixit.id,
                         problem="Keyboard + weak battery", cost=3200, days=3,
                         description="Replace keyboard and battery", status="SENT"))

        # --- Marketplace listings (FR-H): devices, components and materials ---
        db.add_all([
            # Whole devices
            ResaleListing(device_id=d_ip12.id, seller_id=consumer.id, kind="device", type="smartphone",
                          title="Apple iPhone 12", price=22000, quantity=1, condition="Good",
                          description="Fully functional, minor wear.", status="ACTIVE"),
            ResaleListing(seller_id=consumer.id, kind="device", type="laptop",
                          title="Lenovo ThinkPad T480", price=18500, quantity=1, condition="Refurbished",
                          description="Professionally refurbished, 6-month warranty.", status="ACTIVE"),
            # Components
            ResaleListing(seller_id=consumer.id, kind="component", type="gpu",
                          title="NVIDIA RTX 3060 Graphics Card", price=18000, quantity=1, condition="Good",
                          description="Pulled from a working PC, no artifacts.", status="ACTIVE"),
            ResaleListing(seller_id=consumer.id, kind="component", type="ram",
                          title="Corsair 16GB DDR4 RAM", price=2800, quantity=4, condition="Good",
                          description="Tested modules, 3200MHz.", status="ACTIVE"),
            ResaleListing(seller_id=consumer.id, kind="component", type="storage",
                          title="Samsung 1TB SSD (secondary storage)", price=4500, quantity=2, condition="Good",
                          description="Healthy SSDs, 95%+ life remaining.", status="ACTIVE"),
            # Recovered materials — sold by quantity / in bulk
            ResaleListing(seller_id=consumer.id, kind="material", type="copper",
                          title="Recovered copper (from cables)", price=650, unit="kg",
                          quantity=120, min_order=5, condition="Recovered",
                          description="99% pure copper recovered from e-waste wiring.", status="ACTIVE"),
            ResaleListing(seller_id=consumer.id, kind="material", type="aluminium",
                          title="Aluminium scrap (chassis)", price=180, unit="kg",
                          quantity=300, min_order=10, condition="Recovered",
                          description="Clean aluminium from laptop/desktop chassis.", status="ACTIVE"),
            ResaleListing(seller_id=consumer.id, kind="material", type="rare_earth",
                          title="Rare-earth magnet material (neodymium)", price=45, unit="g",
                          quantity=2000, min_order=50, condition="Recovered",
                          description="Neodymium recovered from hard-drive magnets.", status="ACTIVE"),
            ResaleListing(seller_id=consumer.id, kind="material", type="gold",
                          title="Gold recovered from connectors", price=6200, unit="g",
                          quantity=40, min_order=1, condition="Recovered",
                          description="Fine gold recovered from board connectors and pins.", status="ACTIVE"),
        ])

        # --- Lifecycle events (FR-J) ---
        base = datetime.utcnow()
        db.add_all([
            LifecycleEvent(device_id=d_xps.id, type="DEVICE_REGISTERED",
                           description="Device registered on the platform", actor="Priya",
                           timestamp=base - timedelta(days=20)),
            LifecycleEvent(device_id=d_xps.id, type="CONDITION_ASSESSED",
                           description="Condition assessed → recommendation: REPAIR", actor="Priya",
                           timestamp=base - timedelta(days=19)),
            LifecycleEvent(device_id=d_xps.id, type="QUOTE_REQUESTED",
                           description="Quotation requested from FixIt Labs", actor="Priya",
                           timestamp=base - timedelta(days=2)),
            LifecycleEvent(device_id=d_ip12.id, type="DEVICE_REGISTERED",
                           description="Device registered on the platform", actor="Priya",
                           timestamp=base - timedelta(days=12)),
            LifecycleEvent(device_id=d_ip12.id, type="LISTED_FOR_RESALE",
                           description="Listed for resale at ₹22,000", actor="Priya",
                           timestamp=base - timedelta(days=3)),
            LifecycleEvent(device_id=d_tab.id, type="DEVICE_REGISTERED",
                           description="Device registered on the platform", actor="Priya",
                           timestamp=base - timedelta(days=5)),
        ])

        # --- Material reference prices (Feature 2) ---
        # These are ADMIN-SET DEMO REFERENCES, not market data: they are labelled
        # as such in `source`, are never reported as "live", and an admin can
        # change them (or connect a real feed via PRICE_API_BASE_URL).
        demo_source = "Admin reference — demo seed value, not market data"
        refs = [
            ("copper", "Copper", "750", "kg"),
            ("aluminium", "Aluminium", "200", "kg"),
            ("gold", "Gold", "6500", "g"),
            ("rare_earth", "Rare-earth (neodymium)", "40", "g"),
            ("silicon", "Silicon", "250", "kg"),
        ]
        for material, name, price, unit in refs:
            db.add(MaterialPrice(material=material, display_name=name, reference_price=Decimal(price),
                                 currency="INR", unit=unit, source=demo_source, source_type="admin",
                                 observed_at=base, updated_at=base, updated_by=admin.id,
                                 band_min=Decimal("0.5"), band_max=Decimal("1.5"), extreme_max=Decimal("3")))
            db.add(MaterialPriceHistory(material=material, reference_price=Decimal(price), currency="INR",
                                        unit=unit, source=demo_source, source_type="admin",
                                        observed_at=base, recorded_by=admin.id))

        # --- Category references for the resale estimate ---
        # ADMIN-SET DEMO VALUES, not market data (labelled as such; admins edit
        # them in Admin → Device pricing). Only used when the seller doesn't say
        # what they paid.
        categories = [
            # category, kind, name, typical new ₹, depreciation/yr
            ("smartphone", "device", "Smartphone", "45000", "0.25"),
            ("laptop", "device", "Laptop", "70000", "0.20"),
            ("tablet", "device", "Tablet", "30000", "0.22"),
            ("cpu", "component", "CPU", "20000", "0.15"),
            ("gpu", "component", "Graphics card", "35000", "0.18"),
            ("ram", "component", "RAM", "5000", "0.20"),
            ("motherboard", "component", "Motherboard", "12000", "0.18"),
            ("storage", "component", "Storage drive", "7000", "0.25"),
            ("cooler", "component", "Cooler", "4000", "0.12"),
        ]
        for category, kind, name, price, dep in categories:
            db.add(CategoryPrice(category=category, kind=kind, display_name=name,
                                 typical_new_price=Decimal(price), annual_depreciation=Decimal(dep),
                                 residual_floor=Decimal("0.1"), source=demo_source,
                                 observed_at=base, updated_at=base, updated_by=admin.id))

        # --- Flagged listings (Feature 4): one REVIEW, one EXTREME, awaiting an admin ---
        l_review = ResaleListing(seller_id=consumer.id, kind="material", type="copper",
                                 title="Oxygen-free copper wire (audio grade)", price=1500, unit="kg",
                                 quantity=20, min_order=1, condition="Recovered",
                                 description="OFC copper recovered from premium audio cabling.",
                                 status="PRICE_REVIEW_REQUIRED")
        l_extreme = ResaleListing(seller_id=consumer.id, kind="material", type="gold",
                                  title="Gold flakes (connector recovery)", price=25000, unit="g",
                                  quantity=5, min_order=1, condition="Recovered",
                                  description="Small gold flakes.", status="SUSPENDED_PENDING_REVIEW")
        db.add_all([l_review, l_extreme])
        db.flush()
        db.add_all([
            PriceReview(listing_id=l_review.id, seller_id=consumer.id, material="copper", level="REVIEW",
                        listed_price=Decimal("1500"), listed_unit="kg", reference_price=Decimal("750"),
                        reference_unit="kg", ratio=Decimal("2"),
                        reason="Price is 2× the reference (normal band 0.5×–1.5×). Add a justification; an admin will review it.",
                        justification="Oxygen-free audio-grade copper sells at a premium over scrap copper.",
                        created_at=base - timedelta(hours=5)),
            PriceReview(listing_id=l_extreme.id, seller_id=consumer.id, material="gold", level="EXTREME",
                        listed_price=Decimal("25000"), listed_unit="g", reference_price=Decimal("6500"),
                        reference_unit="g", ratio=Decimal("3.846"),
                        reason="Price is 3.846× the reference — above the 3× limit. The listing is held until an admin reviews it.",
                        created_at=base - timedelta(hours=3)),
            Notification(user_id=admin.id, type="price", title="Price review needed (EXTREME)",
                         message="“Gold flakes (connector recovery)” was flagged at 3.846× the reference.",
                         meta={"listing_id": l_extreme.id}, created_at=base - timedelta(hours=3)),
        ])

        # --- Notifications (Feature 3): a few so the bell has content in the demo ---
        db.add_all([
            Notification(user_id=consumer.id, type="quote", title="Quote received",
                         message="FixIt Labs sent a quote of ₹3,200 for your Dell XPS 13.",
                         meta={"device_id": d_xps.id}, created_at=base - timedelta(days=2)),
            Notification(user_id=consumer.id, type="system", title="Welcome to the marketplace",
                         message="Your account is verified. You can now list and buy items.",
                         read=True, read_at=base - timedelta(days=19), created_at=base - timedelta(days=20)),
            Notification(user_id=provider_user.id, type="quote", title="New quote request",
                         message="Priya Sharma requested a quote for a Dell XPS 13.",
                         meta={"device_id": d_xps.id}, created_at=base - timedelta(days=2)),
        ])

        db.commit()
        print("Seed complete.")
        print(f"  roles={db.query(Role).count()} users={db.query(User).count()} "
              f"providers={db.query(Provider).count()} devices={db.query(Device).count()} "
              f"listings={db.query(ResaleListing).count()} "
              f"lifecycle_events={db.query(LifecycleEvent).count()}")
        print("Demo login: demo.user@example.com / password123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
