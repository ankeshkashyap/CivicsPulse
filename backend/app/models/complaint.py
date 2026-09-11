import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Enum,
    ForeignKey,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry, WKTElement
from geoalchemy2.shape import to_shape
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
    Location is canonically stored as a PostGIS POINT geometry (EPSG:4326),
    serving as the single authoritative source of truth.
    """
    __tablename__ = "complaints"


    city_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
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

    # Canonical PostGIS Point geometry (SRID 4326) - Single Source of Truth
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    location_source: Mapped[str] = mapped_column(
        String(50),
        default="MANUAL",
        nullable=False,
    )

    def __init__(self, *args, **kwargs):
        # Support initializing with latitude and longitude transparently
        lat = kwargs.pop("latitude", None)
        lon = kwargs.pop("longitude", None)
        if "location" not in kwargs and lat is not None and lon is not None:
            kwargs["location"] = WKTElement(f"POINT({lon} {lat})", srid=4326)
        super().__init__(*args, **kwargs)

    @property
    def latitude(self) -> Optional[Decimal]:
        """Derived latitude coordinate extracted from canonical PostGIS location."""
        if self.location is not None:
            try:
                shape = to_shape(self.location)
                return Decimal(str(round(shape.y, 6)))
            except Exception:
                pass
        return None

    @latitude.setter
    def latitude(self, value: Decimal | float) -> None:
        current_lon = self.longitude or Decimal("0.0")
        self.location = WKTElement(f"POINT({current_lon} {value})", srid=4326)

    @property
    def longitude(self) -> Optional[Decimal]:
        """Derived longitude coordinate extracted from canonical PostGIS location."""
        if self.location is not None:
            try:
                shape = to_shape(self.location)
                return Decimal(str(round(shape.x, 6)))
            except Exception:
                pass
        return None

    @longitude.setter
    def longitude(self, value: Decimal | float) -> None:
        current_lat = self.latitude or Decimal("0.0")
        self.location = WKTElement(f"POINT({value} {current_lat})", srid=4326)

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