import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.city import City
    from app.models.complaint import Complaint


class Department(Base, UUIDMixin, TimestampMixin):
    """
    Municipal Department within a city (e.g. Roads, Sanitation, Public Works).
    """
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("city_id", "name", name="uq_departments_city_id_name"),
    )

    city_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    city: Mapped["City"] = relationship(
        "City",
        back_populates="departments",
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="department",
    )