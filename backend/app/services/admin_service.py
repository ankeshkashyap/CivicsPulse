import logging
import uuid
from typing import Dict, List, Optional, Set, Tuple
from fastapi import HTTPException, status
from sqlalchemy import cast, func, literal, or_, select, String
from sqlalchemy.orm import Session, selectinload

from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_image import ComplaintImage
from app.models.complaint_update import ComplaintUpdate
from app.models.department import Department
from app.models.enums import (
    ComplaintActionType,
    ComplaintCategory,
    ComplaintSeverity,
    ComplaintStatus,
    UserRole,
)
from app.models.upvote import Upvote
from app.models.user import User
from app.schemas.admin import (
    AdminComplaintDetailResponse,
    AdminComplaintListItemResponse,
    AdminDashboardStatsResponse,
)
from app.schemas.complaint import ComplaintImageResponse, ComplaintUpdateResponse
from app.services.priority_service import (
    calculate_priority_score,
    get_severity_weight,
    get_severity_weight_sql,
)

logger = logging.getLogger(__name__)

# Central authoritative lifecycle progress mapping
STATUS_PROGRESS_MAPPING: Dict[ComplaintStatus, int] = {
    ComplaintStatus.SUBMITTED: 0,
    ComplaintStatus.UNDER_REVIEW: 25,
    ComplaintStatus.ASSIGNED: 50,
    ComplaintStatus.IN_PROGRESS: 75,
    ComplaintStatus.RESOLVED: 100,
    ComplaintStatus.REJECTED: 0,
}

# Approved municipal lifecycle transition rules
VALID_TRANSITIONS: Dict[ComplaintStatus, Set[ComplaintStatus]] = {
    ComplaintStatus.SUBMITTED: {ComplaintStatus.UNDER_REVIEW},
    ComplaintStatus.UNDER_REVIEW: {ComplaintStatus.ASSIGNED, ComplaintStatus.REJECTED},
    ComplaintStatus.ASSIGNED: {ComplaintStatus.IN_PROGRESS},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.RESOLVED},
    ComplaintStatus.RESOLVED: set(),
    ComplaintStatus.REJECTED: set(),
}


def _format_update_actor(update: ComplaintUpdate, complaint_author_id: uuid.UUID) -> Tuple[str, str]:
    """Generates privacy-safe actor role and display label."""
    if update.updated_by_user_id == complaint_author_id:
        return "CITIZEN", "Citizen (Reporter)"
    if update.updated_by_user and update.updated_by_user.full_name:
        return "ADMIN", f"Admin ({update.updated_by_user.full_name})"
    return "ADMIN", "Municipal Officer"


def _build_admin_complaint_item(
    complaint: Complaint,
    upvote_count: int,
    city_name: str,
    department_name: Optional[str] = None,
) -> AdminComplaintListItemResponse:
    """Builds a standardized AdminComplaintListItemResponse."""
    score = calculate_priority_score(complaint.severity, upvote_count)
    images = complaint.images or []
    thumbnail_url = images[0].image_url if images else None

    return AdminComplaintListItemResponse(
        id=complaint.id,
        title=complaint.title,
        description=complaint.description[:180] + ("..." if len(complaint.description) > 180 else ""),
        category=complaint.category,
        severity=complaint.severity,
        status=complaint.status,
        city_id=complaint.city_id,
        city_name=city_name,
        department_id=complaint.department_id,
        department_name=department_name,
        latitude=float(complaint.latitude or 0.0),
        longitude=float(complaint.longitude or 0.0),
        location_source=complaint.location_source,
        image_count=len(images),
        thumbnail_url=thumbnail_url,
        upvote_count=upvote_count,
        priority_score=score,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
    )


def get_admin_dashboard_stats(
    db: Session,
    city_id: Optional[uuid.UUID] = None,
) -> AdminDashboardStatsResponse:
    """Computes real municipal operations dashboard statistics."""
    base_filter = []
    if city_id:
        base_filter.append(Complaint.city_id == city_id)

    total_complaints = db.scalar(
        select(func.count(Complaint.id)).where(*base_filter)
    ) or 0

    def count_by_status(s: ComplaintStatus) -> int:
        return db.scalar(
            select(func.count(Complaint.id)).where(Complaint.status == s, *base_filter)
        ) or 0

    def count_by_severity(sev: ComplaintSeverity) -> int:
        return db.scalar(
            select(func.count(Complaint.id)).where(Complaint.severity == sev, *base_filter)
        ) or 0

    submitted = count_by_status(ComplaintStatus.SUBMITTED)
    under_review = count_by_status(ComplaintStatus.UNDER_REVIEW)
    assigned = count_by_status(ComplaintStatus.ASSIGNED)
    in_progress = count_by_status(ComplaintStatus.IN_PROGRESS)
    resolved = count_by_status(ComplaintStatus.RESOLVED)
    rejected = count_by_status(ComplaintStatus.REJECTED)

    high_sev = count_by_severity(ComplaintSeverity.HIGH)
    med_sev = count_by_severity(ComplaintSeverity.MEDIUM)
    low_sev = count_by_severity(ComplaintSeverity.LOW)

    # Open unassigned complaints
    unassigned = db.scalar(
        select(func.count(Complaint.id)).where(
            Complaint.department_id.is_(None),
            Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW]),
            *base_filter,
        )
    ) or 0

    # High priority open complaints (open complaints with priority >= 50 or severity HIGH)
    upvote_counts_subq = (
        select(Upvote.complaint_id, func.count(Upvote.id).label("upvote_count"))
        .group_by(Upvote.complaint_id)
        .subquery()
    )
    priority_score_expr = (
        func.coalesce(upvote_counts_subq.c.upvote_count, 0) + get_severity_weight_sql(Complaint.severity)
    )

    open_statuses = [
        ComplaintStatus.SUBMITTED,
        ComplaintStatus.UNDER_REVIEW,
        ComplaintStatus.ASSIGNED,
        ComplaintStatus.IN_PROGRESS,
    ]

    high_priority_count = db.scalar(
        select(func.count(Complaint.id))
        .outerjoin(upvote_counts_subq, Complaint.id == upvote_counts_subq.c.complaint_id)
        .where(
            Complaint.status.in_(open_statuses),
            priority_score_expr >= 50,
            *base_filter,
        )
    ) or 0

    # Recent highest-priority unresolved complaints
    priority_stmt = (
        select(
            Complaint,
            func.coalesce(upvote_counts_subq.c.upvote_count, 0).label("upvote_count"),
            City.name.label("city_name"),
            Department.name.label("department_name"),
        )
        .join(City, Complaint.city_id == City.id)
        .outerjoin(Department, Complaint.department_id == Department.id)
        .outerjoin(upvote_counts_subq, Complaint.id == upvote_counts_subq.c.complaint_id)
        .where(Complaint.status.in_(open_statuses), *base_filter)
        .options(selectinload(Complaint.images))
        .order_by(priority_score_expr.desc(), Complaint.created_at.desc())
        .limit(5)
    )
    priority_rows = db.execute(priority_stmt).all()

    recent_priority_complaints = [
        _build_admin_complaint_item(row[0], row[1], row[2], row[3])
        for row in priority_rows
    ]

    return AdminDashboardStatsResponse(
        total_complaints=total_complaints,
        submitted_count=submitted,
        under_review_count=under_review,
        assigned_count=assigned,
        in_progress_count=in_progress,
        resolved_count=resolved,
        rejected_count=rejected,
        high_severity_count=high_sev,
        medium_severity_count=med_sev,
        low_severity_count=low_sev,
        high_priority_count=high_priority_count,
        unassigned_count=unassigned,
        recent_priority_complaints=recent_priority_complaints,
    )


def get_admin_complaints(
    db: Session,
    search: Optional[str] = None,
    status_filter: Optional[ComplaintStatus] = None,
    severity_filter: Optional[ComplaintSeverity] = None,
    category_filter: Optional[ComplaintCategory] = None,
    department_id: Optional[uuid.UUID] = None,
    city_id: Optional[uuid.UUID] = None,
    min_priority: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[AdminComplaintListItemResponse], int]:
    """Retrieves a filtered, priority-sorted list of complaints for municipal administrators."""
    upvote_counts_subq = (
        select(Upvote.complaint_id, func.count(Upvote.id).label("upvote_count"))
        .group_by(Upvote.complaint_id)
        .subquery()
    )

    priority_score_expr = (
        func.coalesce(upvote_counts_subq.c.upvote_count, 0) + get_severity_weight_sql(Complaint.severity)
    )

    conditions = []
    if status_filter:
        conditions.append(Complaint.status == status_filter)
    if severity_filter:
        conditions.append(Complaint.severity == severity_filter)
    if category_filter:
        conditions.append(Complaint.category == category_filter)
    if department_id:
        conditions.append(Complaint.department_id == department_id)
    if city_id:
        conditions.append(Complaint.city_id == city_id)
    if min_priority is not None:
        conditions.append(priority_score_expr >= min_priority)

    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append(
            or_(
                Complaint.title.ilike(term),
                Complaint.description.ilike(term),
                cast(Complaint.id, String).ilike(term),
            )
        )

    # Count total matching
    count_stmt = (
        select(func.count(Complaint.id))
        .outerjoin(upvote_counts_subq, Complaint.id == upvote_counts_subq.c.complaint_id)
        .where(*conditions)
    )
    total_count = db.scalar(count_stmt) or 0

    # Query paginated rows
    stmt = (
        select(
            Complaint,
            func.coalesce(upvote_counts_subq.c.upvote_count, 0).label("upvote_count"),
            City.name.label("city_name"),
            Department.name.label("department_name"),
        )
        .join(City, Complaint.city_id == City.id)
        .outerjoin(Department, Complaint.department_id == Department.id)
        .outerjoin(upvote_counts_subq, Complaint.id == upvote_counts_subq.c.complaint_id)
        .where(*conditions)
        .options(selectinload(Complaint.images))
        .order_by(priority_score_expr.desc(), Complaint.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(stmt).all()

    items = [
        _build_admin_complaint_item(row[0], row[1], row[2], row[3])
        for row in rows
    ]

    return items, total_count


def get_admin_complaint_detail(
    db: Session,
    complaint_id: uuid.UUID,
) -> AdminComplaintDetailResponse:
    """Retrieves comprehensive complaint detail and complete structured audit trail."""
    complaint = db.scalar(
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(
            selectinload(Complaint.city),
            selectinload(Complaint.department),
            selectinload(Complaint.images),
            selectinload(Complaint.updates).selectinload(ComplaintUpdate.updated_by_user),
            selectinload(Complaint.updates).selectinload(ComplaintUpdate.old_department),
            selectinload(Complaint.updates).selectinload(ComplaintUpdate.new_department),
        )
    )
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    # Build chronological updates list
    updates_response = []
    # Sort updates chronologically
    sorted_updates = sorted(complaint.updates, key=lambda u: u.created_at)
    for u in sorted_updates:
        role, label = _format_update_actor(u, complaint.user_id)
        updates_response.append(
            ComplaintUpdateResponse(
                id=u.id,
                action_type=u.action_type,
                old_status=u.old_status,
                new_status=u.new_status,
                old_severity=u.old_severity,
                new_severity=u.new_severity,
                old_department_id=u.old_department_id,
                old_department_name=u.old_department.name if u.old_department else None,
                new_department_id=u.new_department_id,
                new_department_name=u.new_department.name if u.new_department else None,
                remark=u.remark,
                progress_percentage=u.progress_percentage,
                actor_role=role,
                actor_label=label,
                created_at=u.created_at,
            )
        )

    images_response = [
        ComplaintImageResponse(
            id=img.id,
            image_url=img.image_url,
            public_id=img.public_id,
            latitude=float(img.latitude) if img.latitude is not None else None,
            longitude=float(img.longitude) if img.longitude is not None else None,
            created_at=img.created_at,
        )
        for img in complaint.images
    ]

    upvote_count = db.scalar(
        select(func.count(Upvote.id)).where(Upvote.complaint_id == complaint.id)
    ) or 0
    priority_score = calculate_priority_score(complaint.severity, upvote_count)
    severity_weight = get_severity_weight(complaint.severity)

    city_name = complaint.city.name if complaint.city else "Unknown"
    dept_name = complaint.department.name if complaint.department else None

    return AdminComplaintDetailResponse(
        id=complaint.id,
        title=complaint.title,
        description=complaint.description,
        category=complaint.category,
        severity=complaint.severity,
        status=complaint.status,
        city_id=complaint.city_id,
        city_name=city_name,
        department_id=complaint.department_id,
        department_name=dept_name,
        latitude=float(complaint.latitude or 0.0),
        longitude=float(complaint.longitude or 0.0),
        location_source=complaint.location_source,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        images=images_response,
        updates=updates_response,
        upvote_count=upvote_count,
        priority_score=priority_score,
        severity_weight=severity_weight,
    )


def update_complaint_severity(
    db: Session,
    complaint_id: uuid.UUID,
    new_severity: ComplaintSeverity,
    admin: User,
    remark: Optional[str] = None,
) -> AdminComplaintDetailResponse:
    """Updates complaint severity and logs structured audit entry."""
    complaint = db.scalar(
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(
            selectinload(Complaint.city),
            selectinload(Complaint.department),
            selectinload(Complaint.images),
            selectinload(Complaint.updates),
        )
    )
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if new_severity not in [ComplaintSeverity.LOW, ComplaintSeverity.MEDIUM, ComplaintSeverity.HIGH]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid severity value.",
        )

    old_severity = complaint.severity
    complaint.severity = new_severity

    update_entry = ComplaintUpdate(
        complaint_id=complaint.id,
        updated_by_user_id=admin.id,
        action_type=ComplaintActionType.SEVERITY_CHANGE,
        old_status=complaint.status,
        new_status=complaint.status,
        old_severity=old_severity,
        new_severity=new_severity,
        progress_percentage=STATUS_PROGRESS_MAPPING.get(complaint.status, 0),
        remark=remark or f"Severity updated from {old_severity.value} to {new_severity.value}",
    )
    db.add(update_entry)
    db.commit()

    return get_admin_complaint_detail(db=db, complaint_id=complaint.id)


def assign_complaint_department(
    db: Session,
    complaint_id: uuid.UUID,
    department_id: Optional[uuid.UUID],
    admin: User,
    remark: Optional[str] = None,
) -> AdminComplaintDetailResponse:
    """Assigns or clears complaint department with strict multi-city validation."""
    complaint = db.scalar(
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(
            selectinload(Complaint.city),
            selectinload(Complaint.department),
            selectinload(Complaint.images),
            selectinload(Complaint.updates),
        )
    )
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    # Invariant: Terminal states cannot be mutated through department-assignment
    if complaint.status in (ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify department for complaint in terminal state {complaint.status.value}.",
        )

    # Invariant: ASSIGNED and IN_PROGRESS require an assigned department (cannot be unassigned)
    if department_id is None and complaint.status in (ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot unassign department while complaint is in {complaint.status.value} status.",
        )

    old_department_id = complaint.department_id

    if department_id is not None:
        dept = db.scalar(select(Department).where(Department.id == department_id))
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found.",
            )
        if not dept.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department is inactive.",
            )
        if dept.city_id != complaint.city_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department belongs to a different city than the complaint.",
            )
        complaint.department_id = dept.id
        dept_name = dept.name
    else:
        complaint.department_id = None
        dept_name = "Unassigned"

    update_entry = ComplaintUpdate(
        complaint_id=complaint.id,
        updated_by_user_id=admin.id,
        action_type=ComplaintActionType.DEPARTMENT_ASSIGNMENT,
        old_status=complaint.status,
        new_status=complaint.status,
        old_department_id=old_department_id,
        new_department_id=complaint.department_id,
        progress_percentage=STATUS_PROGRESS_MAPPING.get(complaint.status, 0),
        remark=remark or f"Department assignment changed to: {dept_name}",
    )
    db.add(update_entry)
    db.commit()

    return get_admin_complaint_detail(db=db, complaint_id=complaint.id)


def transition_complaint_status(
    db: Session,
    complaint_id: uuid.UUID,
    new_status: ComplaintStatus,
    admin: User,
    department_id: Optional[uuid.UUID] = None,
    remark: Optional[str] = None,
) -> AdminComplaintDetailResponse:
    """Transitions complaint through municipal lifecycle states with invariant validation."""
    complaint = db.scalar(
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(
            selectinload(Complaint.city),
            selectinload(Complaint.department),
            selectinload(Complaint.images),
            selectinload(Complaint.updates),
        )
    )
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    old_status = complaint.status
    allowed_transitions = VALID_TRANSITIONS.get(old_status, set())

    if new_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {old_status.value} to {new_status.value}.",
        )

    old_dept_id = complaint.department_id
    new_dept_id = old_dept_id

    # ASSIGNED state invariant: Must have an assigned department
    if new_status == ComplaintStatus.ASSIGNED:
        if department_id is not None:
            dept = db.scalar(select(Department).where(Department.id == department_id))
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department not found.",
                )
            if not dept.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department is inactive.",
                )
            if dept.city_id != complaint.city_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department belongs to a different city than the complaint.",
                )
            complaint.department_id = dept.id
            new_dept_id = dept.id

        if not complaint.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transition complaint to ASSIGNED without an assigned department.",
            )

    complaint.status = new_status
    progress = STATUS_PROGRESS_MAPPING.get(new_status, 0)

    # If department was also changed in this transition, preserve both in the structured event
    update_entry = ComplaintUpdate(
        complaint_id=complaint.id,
        updated_by_user_id=admin.id,
        action_type=ComplaintActionType.STATUS_CHANGE,
        old_status=old_status,
        new_status=new_status,
        old_department_id=old_dept_id if old_dept_id != new_dept_id else None,
        new_department_id=new_dept_id if old_dept_id != new_dept_id else None,
        progress_percentage=progress,
        remark=remark or f"Status transitioned from {old_status.value} to {new_status.value}",
    )
    db.add(update_entry)
    db.commit()

    return get_admin_complaint_detail(db=db, complaint_id=complaint.id)


def add_complaint_progress_remark(
    db: Session,
    complaint_id: uuid.UUID,
    remark: str,
    admin: User,
) -> AdminComplaintDetailResponse:
    """Appends an official operational progress remark."""
    cleaned_remark = (remark or "").strip()
    if len(cleaned_remark) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Progress remark must be at least 3 characters.",
        )

    complaint = db.scalar(
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(
            selectinload(Complaint.city),
            selectinload(Complaint.department),
            selectinload(Complaint.images),
            selectinload(Complaint.updates),
        )
    )
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    update_entry = ComplaintUpdate(
        complaint_id=complaint.id,
        updated_by_user_id=admin.id,
        action_type=ComplaintActionType.PROGRESS_REMARK,
        old_status=complaint.status,
        new_status=complaint.status,
        progress_percentage=STATUS_PROGRESS_MAPPING.get(complaint.status, 0),
        remark=cleaned_remark,
    )
    db.add(update_entry)
    db.commit()

    return get_admin_complaint_detail(db=db, complaint_id=complaint.id)


def get_departments(
    db: Session,
    city_id: Optional[uuid.UUID] = None,
) -> List[Department]:
    """Lists active municipal departments, optionally filtered by city."""
    stmt = select(Department).where(Department.is_active.is_(True))
    if city_id:
        stmt = stmt.where(Department.city_id == city_id)
    stmt = stmt.order_by(Department.name)
    return list(db.scalars(stmt).all())
