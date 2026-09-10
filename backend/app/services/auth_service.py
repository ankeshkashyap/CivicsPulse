import hashlib
import logging
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_otp import AuthOTPChallenge
from app.models.enums import UserRole
from app.models.user import User
from app.services.email_service import get_email_provider
from app.services.jwt_service import create_access_token

logger = logging.getLogger("civicpulse.auth.service")
ph = PasswordHasher()

# In-memory IP request tracking for rate limiting (timestamp lists)
_ip_request_timestamps = defaultdict(list)
IP_RATE_LIMIT_WINDOW = 60  # seconds
IP_RATE_LIMIT_MAX_REQUESTS = 10  # max requests per minute per IP


class AuthError(Exception):
    """Custom authentication exception with status code and detail message."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def generate_otp() -> str:
    """Generates a cryptographically secure 6-digit numeric OTP."""
    code = secrets.randbelow(1_000_000)
    return f"{code:06d}"


def hash_otp(otp: str) -> str:
    """Hashes the OTP code using Argon2id."""
    return ph.hash(otp)


def verify_otp_hash(stored_hash: str, otp: str) -> bool:
    """Safely verifies the OTP code against the Argon2id hash."""
    try:
        return ph.verify(stored_hash, otp)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception as exc:
        logger.warning(f"Unexpected error during OTP hash verification: {exc}")
        return False


def hash_ip(ip_address: Optional[str]) -> Optional[str]:
    """Anonymously hashes IP address for auditing without storing plaintext IP."""
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()[:32]


def to_utc(dt: datetime) -> datetime:
    """Ensures datetime is timezone-aware in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_rate_limits(email: str, ip_address: Optional[str], db: Session) -> None:
    """
    Enforces rate limits on OTP generation:
    1. Per-IP rate limiting (in-memory sliding window)
    2. Per-email cooldown (DB-backed recent challenge creation)
    """
    now = datetime.now(timezone.utc)

    # 1. IP rate limit check
    if ip_address:
        timestamps = _ip_request_timestamps[ip_address]
        # Prune old timestamps
        cutoff = now.timestamp() - IP_RATE_LIMIT_WINDOW
        _ip_request_timestamps[ip_address] = [ts for ts in timestamps if ts > cutoff]
        if len(_ip_request_timestamps[ip_address]) >= IP_RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP hash {hash_ip(ip_address)}")
            raise AuthError("Too many OTP requests", status_code=429)
        _ip_request_timestamps[ip_address].append(now.timestamp())

    # 2. Email cooldown check (DB-backed)
    stmt = (
        select(AuthOTPChallenge)
        .where(AuthOTPChallenge.email == email)
        .order_by(AuthOTPChallenge.created_at.desc())
        .limit(1)
    )
    last_challenge = db.scalars(stmt).first()
    if last_challenge and last_challenge.created_at:
        created = to_utc(last_challenge.created_at)
        elapsed = (now - created).total_seconds()
        if elapsed < settings.OTP_COOLDOWN_SECONDS:
            logger.info(f"Rate limit cooldown active for email: {email} ({elapsed:.1f}s < {settings.OTP_COOLDOWN_SECONDS}s)")
            raise AuthError("Too many OTP requests", status_code=429)


def request_otp(
    email: str,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> str:
    """
    Initiates passwordless OTP authentication.
    Applies enumeration defense: returns generic response regardless of whether
    the account exists or whether inactive accounts are ignored.
    """
    normalized_email = email.strip().lower()
    now = datetime.now(timezone.utc)

    # Apply rate limiting
    check_rate_limits(normalized_email, ip_address, db)

    # Check if existing user is deactivated
    user_stmt = select(User).where(User.email == normalized_email)
    existing_user = db.scalars(user_stmt).first()
    if existing_user and not existing_user.is_active:
        logger.info(f"OTP request for inactive account {normalized_email}; suppressing dispatch")
        # Generic response avoids revealing inactive account state
        return "If the email is eligible, an OTP has been sent."

    # Invalidate / supersede previous unconsumed challenges for this email
    unconsumed_stmt = (
        select(AuthOTPChallenge)
        .where(
            AuthOTPChallenge.email == normalized_email,
            AuthOTPChallenge.consumed_at.is_(None),
        )
    )
    unconsumed_challenges = db.scalars(unconsumed_stmt).all()
    for challenge in unconsumed_challenges:
        # Expire older active challenges immediately
        challenge.expires_at = now

    # Generate new 6-digit OTP
    otp = generate_otp()
    otp_hash = hash_otp(otp)
    expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    # Persist challenge
    challenge_entry = AuthOTPChallenge(
        email=normalized_email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        max_attempts=settings.OTP_MAX_ATTEMPTS,
        request_ip_hash=hash_ip(ip_address),
        user_agent=user_agent[:500] if user_agent else None,
        created_at=now,
    )
    db.add(challenge_entry)
    db.commit()

    # Dispatch email OTP via configured provider
    provider = get_email_provider()
    provider.send_otp(normalized_email, otp)

    return "If the email is eligible, an OTP has been sent."


def verify_otp(
    email: str,
    otp: str,
    db: Session,
) -> Tuple[User, str]:
    """
    Verifies the submitted OTP against active database challenges.
    Handles attempt limiting, single-use marking, citizen provisioning,
    and JWT token issuance.
    """
    normalized_email = email.strip().lower()
    now = datetime.now(timezone.utc)

    # Locate the most recent unconsumed challenge for this email
    stmt = (
        select(AuthOTPChallenge)
        .where(
            AuthOTPChallenge.email == normalized_email,
            AuthOTPChallenge.consumed_at.is_(None),
        )
        .order_by(AuthOTPChallenge.created_at.desc())
        .limit(1)
    )
    challenge = db.scalars(stmt).first()

    if not challenge:
        raise AuthError("Invalid or expired OTP", status_code=400)

    # Check if challenge is locked due to too many attempts
    if challenge.is_locked:
        raise AuthError("Too many OTP attempts", status_code=400)

    # Check if challenge has expired
    if challenge.is_expired(now):
        raise AuthError("Invalid or expired OTP", status_code=400)

    # Verify cryptographic hash of OTP
    is_valid = verify_otp_hash(challenge.otp_hash, otp)
    if not is_valid:
        challenge.attempts += 1
        challenge.last_attempt_at = now
        db.commit()
        if challenge.is_locked:
            raise AuthError("Too many OTP attempts", status_code=400)
        raise AuthError("Invalid or expired OTP", status_code=400)

    # Mark challenge as consumed (single-use)
    challenge.consumed_at = now
    challenge.last_attempt_at = now

    # Retrieve or provision user
    user_stmt = select(User).where(User.email == normalized_email)
    user = db.scalars(user_stmt).first()

    if user:
        if not user.is_active:
            db.commit()
            raise AuthError("Inactive account", status_code=403)
        if not user.is_verified:
            user.is_verified = True
    else:
        # Create new Citizen account
        user = User(
            email=normalized_email,
            role=UserRole.CITIZEN,
            is_active=True,
            is_verified=True,
            city_id=None,
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # Generate JWT token
    token = create_access_token(user_id=user.id, role=user.role.value)
    return user, token


def provision_admin_user(
    email: str,
    db: Session,
    full_name: Optional[str] = None,
) -> User:
    """
    Explicit CLI / operator mechanism to provision an ADMIN user.
    Admin accounts cannot be self-created through the public OTP registration flow.
    """
    normalized_email = email.strip().lower()
    stmt = select(User).where(User.email == normalized_email)
    user = db.scalars(stmt).first()

    if user:
        user.role = UserRole.ADMIN
        user.is_active = True
        user.is_verified = True
        if full_name:
            user.full_name = full_name
        logger.info(f"Existing user {normalized_email} elevated to ADMIN.")
    else:
        user = User(
            email=normalized_email,
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        logger.info(f"New ADMIN user created for {normalized_email}.")

    db.commit()
    db.refresh(user)
    return user
