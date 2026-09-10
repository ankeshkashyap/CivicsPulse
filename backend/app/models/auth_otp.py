import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, validates
from app.db.base import Base, UUIDMixin, CreatedAtMixin


class AuthOTPChallenge(Base, UUIDMixin, CreatedAtMixin):
    """
    Dedicated authentication challenge persistence model.
    Stores cryptographically hashed OTPs with strict lifetime, attempt limits,
    and single-use consumption.
    """
    __tablename__ = "auth_otp_challenges"

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    otp_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )
    consumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    request_ip_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @validates("email")
    def validate_and_normalize_email(self, key: str, address: str) -> str:
        """Stores email in normalized lowercase format."""
        if not address or not address.strip():
            raise ValueError("Email address cannot be empty.")
        return address.strip().lower()

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    @property
    def is_locked(self) -> bool:
        return self.attempts >= self.max_attempts

    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now >= exp
