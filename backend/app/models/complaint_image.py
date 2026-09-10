import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.complaint import Complaint


class ComplaintImage(Base, UUIDMixin, CreatedAtMixin):
    """
    Evidence photo metadata associated with a complaint.
    Designed for Cloudinary integration with EXIF geolocation extraction.
    """
    __tablename__ = "complaint_images"
    __table_args__ = (
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)",
            name="chk_image_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)",
            name="chk_image_longitude",
        ),
    )

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    public_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Optional EXIF GPS coordinates extracted from original file metadata
    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=9, scale=6, asdecimal=True),
        nullable=True,
    )
    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=9, scale=6, asdecimal=True),
        nullable=True,
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="images",
    )