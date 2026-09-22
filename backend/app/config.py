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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
