from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User
    from app.models.complaint import Complaint


class City(Base, UUIDMixin, TimestampMixin):
    """
    Municipal City Entity.
    Supports multi-city deployment with distinct administrative boundaries.
    """
    __tablename__ = "cities"
    __table_args__ = (
        UniqueConstraint("name", "state", "country", name="uq_cities_name_state_country"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    departments: Mapped[List["Department"]] = relationship(
        "Department",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="city",
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="city",
    )