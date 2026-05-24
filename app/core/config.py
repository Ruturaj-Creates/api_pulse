"""
Application settings loaded from environment variables.

Why this file exists:
- Production apps never hard-code secrets (DB passwords, JWT keys).
- pydantic-settings reads .env automatically and validates types.
- One Settings object is shared across the whole app (dependency injection).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration for API Pulse."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App metadata
    app_name: str = "API Pulse"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = (
        "postgresql+asyncpg://pulse_user:pulse_password@localhost:5432/api_pulse"
    )

    # JWT (used in Step 3 — authentication)
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Monitoring
    default_check_interval_seconds: int = 60
    failure_threshold: int = 3
    health_check_timeout_seconds: float = 30.0
    health_check_max_retries: int = 1
    scheduler_tick_seconds: int = 30
    max_concurrent_checks: int = 20

    # Email alerts
    alert_email_mock: bool = True
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "noreply@apipulse.local"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.

    @lru_cache ensures we only parse .env once per process.
    FastAPI will inject this via Depends(get_settings).
    """
    return Settings()
