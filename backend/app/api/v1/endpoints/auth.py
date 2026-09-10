import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.v1.deps import (
    get_current_user,
    require_authenticated_user,
    require_citizen,
    require_admin,
)
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    MessageResponse,
    OTPRequest,
    OTPVerify,
    UserResponse,
)
from app.services.auth_service import (
    AuthError,
    request_otp as service_request_otp,
    verify_otp as service_verify_otp,
)

logger = logging.getLogger("civicpulse.api.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> Optional[str]:
    """Extracts client IP from headers or direct connection."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post(
    "/request-otp",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request a passwordless email verification code",
)
def request_otp(
    payload: OTPRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Dispatches a 6-digit OTP code to the requested email.
    Applies account enumeration defense and rate limiting.
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    try:
        message = service_request_otp(
            email=payload.email,
            db=db,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        return MessageResponse(message=message)
    except AuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )


@router.post(
    "/verify-otp",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify an email OTP and establish authenticated session",
)
def verify_otp(
    payload: OTPVerify,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Verifies the submitted 6-digit OTP code.
    Provisions a new CITIZEN account if new, marks verified, issues JWT,
    and sets a secure HttpOnly cookie.
    """
    try:
        user, token = service_verify_otp(
            email=payload.email,
            otp=payload.otp,
            db=db,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )

    # Set secure HttpOnly cookie for session transport
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_prod,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        token=token,
        message="Authentication successful",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch profile of the currently authenticated user",
)
def get_current_user_profile(
    current_user: User = Depends(require_authenticated_user),
) -> UserResponse:
    """Returns safe user details for the active session without exposing secrets."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Terminate authenticated session and clear cookies",
)
def logout(response: Response) -> MessageResponse:
    """Clears the HttpOnly authentication cookie."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
    )
    return MessageResponse(message="Successfully logged out")


# Verification / Role-check diagnostic endpoints
@router.get(
    "/test-citizen",
    response_model=MessageResponse,
    summary="Verify citizen-only route protection",
)
def test_citizen_access(
    current_user: User = Depends(require_citizen),
) -> MessageResponse:
    return MessageResponse(message=f"Hello citizen {current_user.email}")


@router.get(
    "/test-admin",
    response_model=MessageResponse,
    summary="Verify admin-only route protection",
)
def test_admin_access(
    current_user: User = Depends(require_admin),
) -> MessageResponse:
    return MessageResponse(message=f"Hello admin {current_user.email}")
