from typing import List, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Core
    PROJECT_NAME: str = "CivicPulse API"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # Security & Tokens
    JWT_SECRET_KEY: str = "temporary-dev-secret-key-replace-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 5
    OTP_COOLDOWN_SECONDS: int = 60
    AUTH_COOKIE_NAME: str = "civicpulse_access_token"
    AUTH_COOKIE_SAMESITE: str = "lax"
    AUTH_COOKIE_PATH: str = "/"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database
    # Primary: PostgreSQL + PostGIS (GeoAlchemy2)
    DATABASE_URL: str = "postgresql+psycopg2://USER:PASSWORD@localhost:5432/civicpulse_dev"

    @property
    def sync_database_url(self) -> str:
        """Returns standard sync connection string for Alembic migrations and sync engines."""
        url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        return url

    # Email / SMTP Configuration
    EMAIL_PROVIDER: str = "console"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_USER: str | None = None  # Backward-compatible alias for SMTP_USERNAME
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    EMAIL_FROM: str = "no-reply@civicpulse.org"  # Backward-compatible default / alias
    SMTP_USE_TLS: bool = True

    @model_validator(mode="after")
    def sync_smtp_aliases(self) -> "Settings":
        """Synchronizes SMTP aliases to support both standard and legacy variable names."""
        if self.SMTP_USERNAME and not self.SMTP_USER:
            self.SMTP_USER = self.SMTP_USERNAME
        elif self.SMTP_USER and not self.SMTP_USERNAME:
            self.SMTP_USERNAME = self.SMTP_USER

        if self.SMTP_FROM_EMAIL:
            self.EMAIL_FROM = self.SMTP_FROM_EMAIL
        elif self.EMAIL_FROM and not self.SMTP_FROM_EMAIL:
            self.SMTP_FROM_EMAIL = self.EMAIL_FROM
        return self

    @property
    def effective_smtp_username(self) -> str | None:
        return self.SMTP_USERNAME or self.SMTP_USER

    @property
    def effective_smtp_from_email(self) -> str:
        return self.SMTP_FROM_EMAIL or self.EMAIL_FROM

    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None
    CLOUDINARY_FOLDER: str = "civicpulse/complaints"

    WS_HEARTBEAT_INTERVAL: int = 30


settings = Settings()
