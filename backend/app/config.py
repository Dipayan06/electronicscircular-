"""Application configuration.

Loads settings from environment variables / the .env file (NFR-7: no hardcoded
secrets). Using pydantic-settings gives us typed, validated config in one place.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database. Defaults to a local SQLite file so the app runs with zero setup
    # (NFR-5). Swap to a postgresql+psycopg2://... URL for PostgreSQL.
    DATABASE_URL: str = "sqlite:///./circular.db"

    # Auth (used from Phase 7).
    JWT_SECRET: str = "dev-only-change-me"
    JWT_EXPIRE_MINUTES: int = 120

    # CORS (used from Phase 6).
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- Email verification (Feature 1) ---
    # Dev mode: no real mail server; the OTP is exposed to the account owner via a
    # dev endpoint so verification can be completed locally / over a tunnel. Set
    # EMAIL_DEV_MODE=false and fill SMTP_* to send real emails.
    EMAIL_DEV_MODE: bool = True
    EMAIL_FROM: str = "no-reply@circular.example"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""            # never commit — set via .env only
    OTP_TTL_MINUTES: int = 10          # verification code lifetime
    OTP_MAX_ATTEMPTS: int = 5          # wrong tries before the code is invalidated
    RESEND_COOLDOWN_SECONDS: int = 60  # min gap between resend requests
    RESEND_MAX_PER_HOUR: int = 5       # cap on verification emails per hour

    # --- Pricing (Feature 2) ---
    # Optional real market-data provider. When unset, reference prices are
    # admin-managed (clearly labelled, never shown as "live").
    PRICE_API_BASE_URL: str = ""
    PRICE_API_KEY: str = ""            # never commit — set via .env only
    PRICE_STALE_AFTER_HOURS: int = 24  # older than this → flagged "stale" in the UI

    # --- Demo hosting ---
    # When true, load the demo data (seed.py) on startup, but ONLY if the database
    # is empty (no roles yet). Lets a fresh cloud database (e.g. a new free Render
    # Postgres) come up ready to use without running seed.py by hand.
    SEED_DEMO_DATA: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
