import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin, CreatedAtMixin
from app.models.enums import ComplaintStatus

if TYPE_CHECKING:
    from app.models.complaint import Complaint
    from app.models.user import User


class ComplaintUpdate(Base, UUIDMixin, CreatedAtMixin):
    """
    Immutable audit history log tracking administrative transitions and progress updates.
    """
    __tablename__ = "complaint_updates"
    __table_args__ = (
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="chk_update_progress_percentage",
        ),
    )

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    updated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    old_status: Mapped[Optional[ComplaintStatus]] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status", native_enum=True),
        nullable=True,
    )
    new_status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status", native_enum=True),
        nullable=False,
    )
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="updates",
    )
    updated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="complaint_updates",
    )