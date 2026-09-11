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
from app.models.enums import ComplaintActionType, ComplaintSeverity, ComplaintStatus

if TYPE_CHECKING:
    from app.models.complaint import Complaint
    from app.models.department import Department
    from app.models.user import User


class ComplaintUpdate(Base, UUIDMixin, CreatedAtMixin):
    """
    Append-only audit history log tracking administrative transitions and progress updates.
    
    Architectural Invariant:
    ComplaintUpdate records are strictly append-only. Lifecycle and domain services
    may CREATE history records upon valid status transitions, but must NEVER update
    or delete existing history records.
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
    updated_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[ComplaintActionType] = mapped_column(
        Enum(ComplaintActionType, name="complaint_action_type", native_enum=True),
        default=ComplaintActionType.STATUS_CHANGE,
        server_default="STATUS_CHANGE",
        nullable=False,
    )
    old_status: Mapped[Optional[ComplaintStatus]] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status", native_enum=True),
        nullable=True,
    )
    new_status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status", native_enum=True),
        nullable=False,
    )
    old_severity: Mapped[Optional[ComplaintSeverity]] = mapped_column(
        Enum(ComplaintSeverity, name="complaint_severity", native_enum=True),
        nullable=True,
    )
    new_severity: Mapped[Optional[ComplaintSeverity]] = mapped_column(
        Enum(ComplaintSeverity, name="complaint_severity", native_enum=True),
        nullable=True,
    )
    old_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    new_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
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
    updated_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="complaint_updates",
    )
    old_department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[old_department_id],
    )
    new_department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[new_department_id],
    )