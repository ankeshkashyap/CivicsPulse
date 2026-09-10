import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.complaint import Complaint
    from app.models.user import User


class Upvote(Base, UUIDMixin, CreatedAtMixin):
    """
    Citizen upvote entity contributing to community complaint priority.
    Enforces a single upvote per user-complaint pair.
    """
    __tablename__ = "upvotes"
    __table_args__ = (
        UniqueConstraint("complaint_id", "user_id", name="uq_upvotes_complaint_id_user_id"),
    )

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="upvotes",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="upvotes",
    )