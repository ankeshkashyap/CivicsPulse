import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import ComplaintCategory, ComplaintSeverity, ComplaintStatus

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.department import Department
    from app.models.user import User
    from app.models.complaint_image import ComplaintImage
    from app.models.complaint_update import ComplaintUpdate
    from app.models.upvote import Upvote


class Complaint(Base, UUIDMixin, TimestampMixin):
    """
    Central civic complaint entity.
    Location is temporarily persisted as numeric latitude/longitude,
    architecturally designed for future seamless migration to PostGIS geometry(Point, 4326).
    """
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="chk_complaint_latitude"),
        CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="chk_complaint_longitude"),
    )

    city_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped[ComplaintCategory] = mapped_column(
        Enum(ComplaintCategory, name="complaint_category", native_enum=True),
        nullable=False,
        index=True,
    )
    severity: Mapped[ComplaintSeverity] = mapped_column(
        Enum(ComplaintSeverity, name="complaint_severity", native_enum=True),
        default=ComplaintSeverity.MEDIUM,
        nullable=False,
        index=True,
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status", native_enum=True),
        default=ComplaintStatus.SUBMITTED,
        nullable=False,
        index=True,
    )

    # Temporary coordinate representation (to be migrated to PostGIS geometry)
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(precision=9, scale=6, asdecimal=True),
        nullable=False,
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(precision=9, scale=6, asdecimal=True),
        nullable=False,
    )

    # Relationships
    city: Mapped["City"] = relationship(
        "City",
        back_populates="complaints",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="complaints",
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="complaints",
    )
    images: Mapped[List["ComplaintImage"]] = relationship(
        "ComplaintImage",
        back_populates="complaint",
        cascade="all, delete-orphan",
    )
    updates: Mapped[List["ComplaintUpdate"]] = relationship(
        "ComplaintUpdate",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintUpdate.created_at.asc()",
    )
    upvotes: Mapped[List["Upvote"]] = relationship(
        "Upvote",
        back_populates="complaint",
        cascade="all, delete-orphan",
    )