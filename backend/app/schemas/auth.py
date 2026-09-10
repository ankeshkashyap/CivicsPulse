import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.enums import UserRole


class OTPRequest(BaseModel):
    """Schema for requesting a passwordless email OTP."""
    email: EmailStr

    model_config = ConfigDict(str_strip_whitespace=True)


class OTPVerify(BaseModel):
    """Schema for verifying an email OTP."""
    email: EmailStr
    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit numeric verification code",
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class UserResponse(BaseModel):
    """Safe public representation of a user without sensitive secrets."""
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: UserRole
    city_id: Optional[uuid.UUID] = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Response returned upon successful authentication."""
    user: UserResponse
    message: str = "Authentication successful"
    token: Optional[str] = Field(
        default=None,
        description="JWT access token (also dispatched via secure HttpOnly cookie)",
    )


class MessageResponse(BaseModel):
    """Standardized informational message response."""
    message: str
