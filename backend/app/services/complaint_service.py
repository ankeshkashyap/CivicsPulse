import logging
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from geoalchemy2 import WKTElement

from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_image import ComplaintImage
from app.models.complaint_update import ComplaintUpdate
from app.models.enums import ComplaintCategory, ComplaintSeverity, ComplaintStatus, UserRole
from app.models.upvote import Upvote
from app.models.user import User
from app.schemas.complaint import (
    CitizenDashboardStatsResponse,
    ComplaintDetailResponse,
    ComplaintImageResponse,
    ComplaintListItemResponse,
    ComplaintUpdateResponse,
)
from app.services.exif_service import (
    ImageValidationError,
    extract_exif_gps,
    validate_image_file,
)
from app.services.image_storage import ImageStorageProvider, StoredImageResult
from app.services.priority_service import calculate_priority_score, get_severity_weight_sql

logger = logging.getLogger(__name__)


def _format_update_actor(update: ComplaintUpdate, complaint_author_id: uuid.UUID) -> Tuple[str, str]:
    """Generates privacy-safe actor role and display label without revealing personal identity."""
    if update.updated_by_user_id == complaint_author_id:
        return "CITIZEN", "Citizen (Reporter)"
    return "ADMIN", "Municipal Officer"


def get_or_create_default_city(db: Session) -> City:
    """Ensures at least one active demonstration city (Vijayawada) exists in the database."""
    city = db.scalar(select(City).where(City.name == "Vijayawada"))
    if not city:
        city = City(name="Vijayawada", state="Andhra Pradesh", country="India", is_active=True)
        db.add(city)
        db.flush()
    return city


async def create_complaint(
    db: Session,
    citizen: User,
    title: str,
    description: str,
    category: ComplaintCategory,
    severity: ComplaintSeverity,
    latitude: float,
    longitude: float,
    location_source: str,
    image_files: List[Tuple[str, bytes, str]],  # (filename, bytes, content_type)
    storage_provider: ImageStorageProvider,
) -> Complaint:
    """
    Validates, uploads evidence, and transactionally persists a new citizen complaint
    starting in SUBMITTED status with its initial append-only audit record.
    """
    # 1. Validation of textual fields
    cleaned_title = title.strip()
    if len(cleaned_title) < 5 or len(cleaned_title) > 200:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title must be between 5 and 200 characters.",
        )

    cleaned_description = description.strip()
    if len(cleaned_description) < 10 or len(cleaned_description) > 5000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Description must be between 10 and 5000 characters.",
        )

    # 2. Validation of geographic coordinates
    if not (-90.0 <= latitude <= 90.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Latitude must be between -90.0 and 90.0 degrees.",
        )
    if not (-180.0 <= longitude <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Longitude must be between -180.0 and 180.0 degrees.",
        )

    # 3. Image evidence validation (1 to 3 images required)
    if len(image_files) < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one evidence photo is required to submit a civic complaint.",
        )
    if len(image_files) > 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A maximum of 3 evidence photos may be attached.",
        )

    # Validate image formats, magic bytes, and size before upload
    validated_images = []
    for filename, file_bytes, content_type in image_files:
        try:
            detected_mime = validate_image_file(file_bytes, content_type)
        except ImageValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        # Extract safe EXIF GPS metadata if present
        exif_result = extract_exif_gps(
            file_bytes,
            complaint_latitude=Decimal(str(latitude)),
            complaint_longitude=Decimal(str(longitude)),
        )
        validated_images.append((filename, file_bytes, detected_mime, exif_result))

    # 4. Resolve municipal city context
    city_id = citizen.city_id
    if not city_id:
        default_city = get_or_create_default_city(db)
        city_id = default_city.id

    # 5. External Image Storage Upload
    uploaded_results: List[Tuple[StoredImageResult, Decimal | None, Decimal | None]] = []
    try:
        for filename, file_bytes, detected_mime, exif_res in validated_images:
            stored_result = await storage_provider.upload_image(file_bytes, filename, detected_mime)
            uploaded_results.append((stored_result, exif_res.latitude, exif_res.longitude))
    except Exception as exc:
        # If any upload fails, delete already uploaded images to prevent orphans
        logger.error("Failed during image upload step: %s", exc)
        for stored_result, _, _ in uploaded_results:
            await storage_provider.delete_image(stored_result.public_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store evidence images. Please try again.",
        ) from exc

    # 6. Database Transaction: Complaint + Images + Initial Audit Log
    try:
        complaint = Complaint(
            city_id=city_id,
            user_id=citizen.id,
            title=cleaned_title,
            description=cleaned_description,
            category=category,
            severity=severity,
            status=ComplaintStatus.SUBMITTED,
            location=WKTElement(f"POINT({longitude} {latitude})", srid=4326),
            location_source=location_source or "MANUAL",
        )
        db.add(complaint)
        db.flush()

        # Attach image records
        for stored_result, exif_lat, exif_lon in uploaded_results:
            img = ComplaintImage(
                complaint_id=complaint.id,
                image_url=stored_result.image_url,
                public_id=stored_result.public_id,
                latitude=exif_lat,
                longitude=exif_lon,
            )
            db.add(img)

        # Initial immutable audit log entry
        initial_update = ComplaintUpdate(
            complaint_id=complaint.id,
            updated_by_user_id=citizen.id,
            old_status=None,
            new_status=ComplaintStatus.SUBMITTED,
            remark="Complaint submitted by citizen with location verification and photo evidence.",
            progress_percentage=0,
        )
        db.add(initial_update)

        db.commit()
        db.refresh(complaint)
        return complaint

    except Exception as exc:
        db.rollback()
        logger.exception("Database transaction failed during complaint creation; rolling back images.")
        # Cleanup uploaded images from storage provider
        for stored_result, _, _ in uploaded_results:
            try:
                await storage_provider.delete_image(stored_result.public_id)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create civic complaint record.",
        ) from exc


def get_complaints(
    db: Session,
    current_user: User,
    mine_only: bool = False,
    status_filter: Optional[ComplaintStatus] = None,
    category_filter: Optional[ComplaintCategory] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ComplaintListItemResponse]:
    """
    Returns sanitized complaint records.
    Deterministic community ordering:
        1. priority_score DESC
        2. created_at DESC
    Strictly excludes sensitive citizen data (email, user_id, auth credentials) from community views.
    """
    upvote_counts_subq = (
        select(
            Upvote.complaint_id,
            func.count(Upvote.id).label("cnt"),
        )
        .group_by(Upvote.complaint_id)
        .subquery()
    )

    user_upvotes_subq = (
        select(Upvote.complaint_id)
        .where(Upvote.user_id == current_user.id)
        .subquery()
    )

    severity_weight_expr = get_severity_weight_sql(Complaint.severity)
    upvote_count_expr = func.coalesce(upvote_counts_subq.c.cnt, 0)
    priority_score_expr = upvote_count_expr + severity_weight_expr
    has_upvoted_expr = user_upvotes_subq.c.complaint_id.isnot(None)

    stmt = (
        select(
            Complaint,
            upvote_count_expr.label("upvotes_count"),
            has_upvoted_expr.label("has_upvoted"),
            priority_score_expr.label("priority_score"),
        )
        .outerjoin(upvote_counts_subq, Complaint.id == upvote_counts_subq.c.complaint_id)
        .outerjoin(user_upvotes_subq, Complaint.id == user_upvotes_subq.c.complaint_id)
        .options(selectinload(Complaint.images))
    )

    if mine_only:
        stmt = stmt.where(Complaint.user_id == current_user.id)
        stmt = stmt.order_by(Complaint.created_at.desc())
    else:
        stmt = stmt.order_by(
            priority_score_expr.desc(),
            Complaint.created_at.desc(),
        )

    if status_filter:
        stmt = stmt.where(Complaint.status == status_filter)
    if category_filter:
        stmt = stmt.where(Complaint.category == category_filter)

    stmt = stmt.limit(min(max(1, limit), 100)).offset(max(0, offset))
    rows = db.execute(stmt).all()

    results = []
    for c, upvotes_cnt, user_voted, score in rows:
        preview_url = c.images[0].image_url if c.images else None
        results.append(
            ComplaintListItemResponse(
                id=c.id,
                title=c.title,
                description=c.description,
                category=c.category,
                severity=c.severity,
                status=c.status,
                latitude=float(c.latitude or 0.0),
                longitude=float(c.longitude or 0.0),
                location_source=c.location_source,
                created_at=c.created_at,
                preview_image_url=preview_url,
                images_count=len(c.images),
                upvotes_count=upvotes_cnt,
                has_upvoted=bool(user_voted),
                priority_score=score,
                is_owner=(c.user_id == current_user.id),
            )
        )
    return results


def get_complaint_by_id(
    db: Session,
    complaint_id: uuid.UUID,
    current_user: User,
) -> ComplaintDetailResponse:
    """
    Retrieves complete complaint record with sanitized chronological update history,
    upvote count, citizen upvote state, and priority score.
    """
    stmt = (
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(
            selectinload(Complaint.images),
            selectinload(Complaint.updates),
        )
    )
    complaint = db.scalar(stmt)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    # Sanitize update history
    updates_response = []
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

    has_upvoted = False
    if current_user and current_user.role == UserRole.CITIZEN:
        has_upvoted = bool(
            db.scalar(
                select(Upvote.id).where(
                    Upvote.complaint_id == complaint.id,
                    Upvote.user_id == current_user.id,
                )
            )
        )

    score = calculate_priority_score(complaint.severity, upvote_count)

    return ComplaintDetailResponse(
        id=complaint.id,
        title=complaint.title,
        description=complaint.description,
        category=complaint.category,
        severity=complaint.severity,
        status=complaint.status,
        latitude=float(complaint.latitude or 0.0),
        longitude=float(complaint.longitude or 0.0),
        location_source=complaint.location_source,
        city_id=complaint.city_id,
        department_id=complaint.department_id,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        images=images_response,
        updates=updates_response,
        is_owner=(complaint.user_id == current_user.id),
        upvote_count=upvote_count,
        has_upvoted=has_upvoted,
        priority_score=score,
    )


def get_citizen_dashboard_stats(
    db: Session,
    citizen: User,
) -> CitizenDashboardStatsResponse:
    """Computes real aggregate metrics and recent complaints for the logged-in citizen."""
    user_id = citizen.id

    total = db.scalar(
        select(func.count(Complaint.id)).where(Complaint.user_id == user_id)
    ) or 0

    in_progress = db.scalar(
        select(func.count(Complaint.id)).where(
            Complaint.user_id == user_id,
            Complaint.status.in_([
                ComplaintStatus.UNDER_REVIEW,
                ComplaintStatus.ASSIGNED,
                ComplaintStatus.IN_PROGRESS,
            ]),
        )
    ) or 0

    resolved = db.scalar(
        select(func.count(Complaint.id)).where(
            Complaint.user_id == user_id,
            Complaint.status == ComplaintStatus.RESOLVED,
        )
    ) or 0

    rejected = db.scalar(
        select(func.count(Complaint.id)).where(
            Complaint.user_id == user_id,
            Complaint.status == ComplaintStatus.REJECTED,
        )
    ) or 0

    # Total community upvotes received on all complaints submitted by this citizen
    community_upvotes = db.scalar(
        select(func.count(Upvote.id))
        .join(Complaint, Upvote.complaint_id == Complaint.id)
        .where(Complaint.user_id == user_id)
    ) or 0

    # Recent complaints for dashboard preview
    recent_items = get_complaints(
        db=db,
        current_user=citizen,
        mine_only=True,
        limit=5,
        offset=0,
    )

    return CitizenDashboardStatsResponse(
        total_submitted=total,
        in_progress=in_progress,
        resolved=resolved,
        rejected=rejected,
        community_upvotes=community_upvotes,
        recent_complaints=recent_items,
    )
