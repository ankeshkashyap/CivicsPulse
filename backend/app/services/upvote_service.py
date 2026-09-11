import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.enums import UserRole
from app.models.upvote import Upvote
from app.models.user import User
from app.schemas.complaint import UpvoteResponse
from app.services.priority_service import calculate_priority_score


def add_upvote(
    db: Session,
    complaint_id: uuid.UUID,
    citizen: User,
) -> UpvoteResponse:
    """
    Persists an upvote by the authenticated citizen for the given complaint.
    Enforces uniqueness at both application and database constraint levels.
    Safely catches concurrent duplicate attempts and returns HTTP 409 Conflict.
    """
    complaint = db.scalar(select(Complaint).where(Complaint.id == complaint_id))
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    # Fast-path duplicate check
    existing = db.scalar(
        select(Upvote).where(
            Upvote.complaint_id == complaint_id,
            Upvote.user_id == citizen.id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already upvoted this complaint.",
        )

    upvote = Upvote(complaint_id=complaint_id, user_id=citizen.id)
    db.add(upvote)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already upvoted this complaint.",
        )

    count = db.scalar(
        select(func.count(Upvote.id)).where(Upvote.complaint_id == complaint_id)
    ) or 0
    score = calculate_priority_score(complaint.severity, count)

    return UpvoteResponse(
        complaint_id=complaint_id,
        has_upvoted=True,
        upvote_count=count,
        priority_score=score,
    )


def remove_upvote(
    db: Session,
    complaint_id: uuid.UUID,
    citizen: User,
) -> UpvoteResponse:
    """
    Removes the authenticated citizen's upvote on the given complaint.
    Returns HTTP 404 Not Found if no upvote existed.
    """
    complaint = db.scalar(select(Complaint).where(Complaint.id == complaint_id))
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    upvote = db.scalar(
        select(Upvote).where(
            Upvote.complaint_id == complaint_id,
            Upvote.user_id == citizen.id,
        )
    )
    if not upvote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not upvoted this complaint.",
        )

    db.delete(upvote)
    db.commit()

    count = db.scalar(
        select(func.count(Upvote.id)).where(Upvote.complaint_id == complaint_id)
    ) or 0
    score = calculate_priority_score(complaint.severity, count)

    return UpvoteResponse(
        complaint_id=complaint_id,
        has_upvoted=False,
        upvote_count=count,
        priority_score=score,
    )


def get_upvote_status(
    db: Session,
    complaint_id: uuid.UUID,
    current_user: Optional[User] = None,
) -> UpvoteResponse:
    """
    Retrieves current upvote count, priority score, and whether the current user has upvoted.
    """
    complaint = db.scalar(select(Complaint).where(Complaint.id == complaint_id))
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    count = db.scalar(
        select(func.count(Upvote.id)).where(Upvote.complaint_id == complaint_id)
    ) or 0

    has_upvoted = False
    if current_user and current_user.role == UserRole.CITIZEN:
        has_upvoted = bool(
            db.scalar(
                select(Upvote.id).where(
                    Upvote.complaint_id == complaint_id,
                    Upvote.user_id == current_user.id,
                )
            )
        )

    score = calculate_priority_score(complaint.severity, count)

    return UpvoteResponse(
        complaint_id=complaint_id,
        has_upvoted=has_upvoted,
        upvote_count=count,
        priority_score=score,
    )
