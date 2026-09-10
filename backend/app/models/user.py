import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.complaint import Complaint
    from app.models.complaint_update import ComplaintUpdate
    from app.models.upvote import Upvote


class User(Base, UUIDMixin, TimestampMixin):
    """
    User entity supporting passwordless email-OTP authentication.
    Roles are segregated between CITIZEN and ADMIN.
    """
    __tablename__ = "users"

    city_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        default=UserRole.CITIZEN,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @validates("email")
    def validate_and_normalize_email(self, key: str, address: str) -> str:
        """Stores email in normalized lowercase format."""
        if not address or not address.strip():
            raise ValueError("Email address cannot be empty.")
        return address.strip().lower()

    # Relationships
    city: Mapped[Optional["City"]] = relationship(
        "City",
        back_populates="users",
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="user",
    )
    complaint_updates: Mapped[List["ComplaintUpdate"]] = relationship(
        "ComplaintUpdate",
        back_populates="updated_by_user",
    )
    upvotes: Mapped[List["Upvote"]] = relationship(
        "Upvote",
        back_populates="user",
        cascade="all, delete-orphan",
    )