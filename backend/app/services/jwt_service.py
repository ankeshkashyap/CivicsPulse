import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from app.core.config import settings


class JWTError(Exception):
    """Base exception for JWT processing failures."""
    pass


class TokenExpiredError(JWTError):
    """Raised when an access token has expired."""
    pass


class InvalidTokenError(JWTError):
    """Raised when an access token is structurally invalid or signature check fails."""
    pass


def create_access_token(
    user_id: uuid.UUID | str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT access token containing minimal necessary claims.
    Sub is user UUID, role is CITIZEN or ADMIN.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": str(role),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a signed JWT access token.
    Raises TokenExpiredError or InvalidTokenError on failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "role", "exp", "iat"]},
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("Authentication token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Invalid authentication token") from exc
