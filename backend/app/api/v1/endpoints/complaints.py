import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.deps import require_authenticated_user, require_citizen
from app.core.rate_limit import check_complaint_rate_limit
from app.db.session import get_db
from app.models.enums import ComplaintCategory, ComplaintSeverity, ComplaintStatus
from app.models.user import User
from app.schemas.complaint import (
    CitizenDashboardStatsResponse,
    ComplaintDetailResponse,
    ComplaintListItemResponse,
    UpvoteResponse,
)
from app.services.complaint_service import (
    create_complaint,
    get_citizen_dashboard_stats,
    get_complaint_by_id,
    get_complaints,
)
from app.services.image_storage import get_image_storage_provider
from app.services.upvote_service import add_upvote, get_upvote_status, remove_upvote

router = APIRouter()


@router.post(
    "",
    response_model=ComplaintDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a verified civic complaint",
    description="Allows authenticated citizens to report civic issues with PostGIS coordinates and mandatory evidence photos.",
)
async def submit_complaint(
    title: str = Form(..., description="Short summary of the civic problem (5-200 chars)"),
    description: str = Form(..., description="Detailed description of the issue (10-5000 chars)"),
    category: ComplaintCategory = Form(..., description="Municipal category of the problem"),
    severity: ComplaintSeverity = Form(ComplaintSeverity.MEDIUM, description="Citizen-suggested severity"),
    latitude: float = Form(..., description="Geographic latitude coordinate (-90 to 90)"),
    longitude: float = Form(..., description="Geographic longitude coordinate (-180 to 180)"),
    location_source: str = Form("MANUAL", description="Source of coordinates: GPS, EXIF, or MANUAL"),
    images: List[UploadFile] = File(..., description="1 to 3 photo evidence files (JPEG, PNG, WebP)"),
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
):
    # 1. Enforce process-local submission rate limit per citizen
    check_complaint_rate_limit(f"user:{current_user.id}")

    # 2. Read attached upload files
    image_payloads = []
    for upload in images:
        content = await upload.read()
        filename = upload.filename or "evidence.jpg"
        content_type = upload.content_type or "image/jpeg"
        image_payloads.append((filename, content, content_type))

    storage_provider = get_image_storage_provider()

    # 3. Create complaint via transactional domain service
    complaint = await create_complaint(
        db=db,
        citizen=current_user,
        title=title,
        description=description,
        category=category,
        severity=severity,
        latitude=latitude,
        longitude=longitude,
        location_source=location_source,
        image_files=image_payloads,
        storage_provider=storage_provider,
    )

    return get_complaint_by_id(db=db, complaint_id=complaint.id, current_user=current_user)


@router.get(
    "",
    response_model=List[ComplaintListItemResponse],
    summary="List civic complaints",
    description="Retrieves a list of sanitized complaints. Citizens can query community feeds or their own submissions.",
)
def list_complaints(
    mine_only: bool = Query(False, description="Filter strictly to current user's complaints"),
    mine: Optional[bool] = Query(None, description="Alias for mine_only"),
    status: Optional[ComplaintStatus] = Query(None, description="Filter by lifecycle status"),
    category: Optional[ComplaintCategory] = Query(None, description="Filter by municipal category"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    effective_mine = mine if mine is not None else mine_only
    return get_complaints(
        db=db,
        current_user=current_user,
        mine_only=effective_mine,
        status_filter=status,
        category_filter=category,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/stats/citizen",
    response_model=CitizenDashboardStatsResponse,
    summary="Citizen personal dashboard statistics",
    description="Computes real submission, progress, and resolution aggregates for the active citizen.",
)
def citizen_stats(
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
):
    return get_citizen_dashboard_stats(db=db, citizen=current_user)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintDetailResponse,
    summary="Get complaint details and history",
    description="Retrieves full problem details, evidence photos, and chronological audit history.",
)
def get_complaint(
    complaint_id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    return get_complaint_by_id(
        db=db,
        complaint_id=complaint_id,
        current_user=current_user,
    )


@router.post(
    "/{complaint_id}/upvote",
    response_model=UpvoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Upvote a civic complaint",
    description="Allows authenticated citizens to upvote a complaint to raise community priority.",
)
def upvote_complaint(
    complaint_id: uuid.UUID,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
):
    return add_upvote(db=db, complaint_id=complaint_id, citizen=current_user)


@router.delete(
    "/{complaint_id}/upvote",
    response_model=UpvoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove an upvote from a civic complaint",
    description="Allows authenticated citizens to rescind an existing upvote.",
)
def remove_complaint_upvote(
    complaint_id: uuid.UUID,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
):
    return remove_upvote(db=db, complaint_id=complaint_id, citizen=current_user)


@router.get(
    "/{complaint_id}/upvote",
    response_model=UpvoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Get upvote status and priority score for a complaint",
    description="Retrieves current upvote count, priority score, and whether the caller has upvoted.",
)
def complaint_upvote_status(
    complaint_id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    return get_upvote_status(db=db, complaint_id=complaint_id, current_user=current_user)
