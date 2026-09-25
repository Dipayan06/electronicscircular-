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

from app.database import Base, engine, SessionLocal
from app import models
from app.models import (
    Role, User, Device, DeviceAssessment, Provider, ProviderService, SparePart,
    Quotation, ResaleListing, LifecycleEvent,
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

        # --- Users ---
        consumer = User(name="Priya Sharma", email="demo.user@example.com",
                        password_hash=hash_password(DEV_PASSWORD), role_id=roles["consumer"].id)
        provider_user = User(name="FixIt Labs", email="demo.provider@example.com",
                             password_hash=hash_password(DEV_PASSWORD), role_id=roles["provider"].id)
        admin = User(name="Site Admin", email="admin@example.com",
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
