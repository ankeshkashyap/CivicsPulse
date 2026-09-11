import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import require_admin
from app.db.session import get_db
from app.models.enums import ComplaintCategory, ComplaintSeverity, ComplaintStatus
from app.models.user import User
from app.schemas.admin import (
    AdminComplaintDetailResponse,
    AdminComplaintListResponse,
    AdminDashboardStatsResponse,
    AdminDepartmentAssignRequest,
    AdminProgressRemarkRequest,
    AdminSeverityUpdateRequest,
    AdminStatusTransitionRequest,
    DepartmentResponse,
)
from app.services.admin_service import (
    add_complaint_progress_remark,
    assign_complaint_department,
    get_admin_complaint_detail,
    get_admin_complaints,
    get_admin_dashboard_stats,
    get_departments,
    transition_complaint_status,
    update_complaint_severity,
)

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=AdminDashboardStatsResponse,
    summary="Get municipal operational dashboard statistics",
    description="Returns live system-wide aggregate metrics, status distributions, and high priority queue items.",
)
def get_dashboard_stats(
    city_id: Optional[uuid.UUID] = Query(None, description="Optional city filter"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_admin_dashboard_stats(db=db, city_id=city_id)


@router.get(
    "/complaints",
    response_model=AdminComplaintListResponse,
    summary="List complaints for administrative triage",
    description="Retrieves a priority-ordered, filterable, and searchable list of municipal complaints.",
)
def list_admin_complaints(
    search: Optional[str] = Query(None, description="Search term matching title, description, or complaint ID"),
    status: Optional[ComplaintStatus] = Query(None, description="Filter by status"),
    severity: Optional[ComplaintSeverity] = Query(None, description="Filter by severity"),
    category: Optional[ComplaintCategory] = Query(None, description="Filter by category"),
    department_id: Optional[uuid.UUID] = Query(None, description="Filter by assigned department ID"),
    city_id: Optional[uuid.UUID] = Query(None, description="Filter by city ID"),
    min_priority: Optional[int] = Query(None, description="Filter by minimum priority score"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, total = get_admin_complaints(
        db=db,
        search=search,
        status_filter=status,
        severity_filter=severity,
        category_filter=category,
        department_id=department_id,
        city_id=city_id,
        min_priority=min_priority,
        limit=limit,
        offset=offset,
    )
    return AdminComplaintListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/complaints/{complaint_id}",
    response_model=AdminComplaintDetailResponse,
    summary="Get detailed complaint inspection for administrators",
    description="Returns complete details, chronological audit history, photos, and location info.",
)
def get_complaint_detail(
    complaint_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_admin_complaint_detail(db=db, complaint_id=complaint_id)


@router.patch(
    "/complaints/{complaint_id}/severity",
    response_model=AdminComplaintDetailResponse,
    summary="Update complaint severity",
    description="Changes complaint severity and automatically recalculates derived priority score.",
)
def patch_complaint_severity(
    complaint_id: uuid.UUID,
    payload: AdminSeverityUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return update_complaint_severity(
        db=db,
        complaint_id=complaint_id,
        new_severity=payload.severity,
        admin=current_user,
        remark=payload.remark,
    )


@router.patch(
    "/complaints/{complaint_id}/department",
    response_model=AdminComplaintDetailResponse,
    summary="Assign or reassign complaint to a department",
    description="Assigns complaint to an active department in the same city, or clears assignment if department_id is null.",
)
def patch_complaint_department(
    complaint_id: uuid.UUID,
    payload: AdminDepartmentAssignRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return assign_complaint_department(
        db=db,
        complaint_id=complaint_id,
        department_id=payload.department_id,
        admin=current_user,
        remark=payload.remark,
    )


@router.patch(
    "/complaints/{complaint_id}/status",
    response_model=AdminComplaintDetailResponse,
    summary="Transition complaint lifecycle status",
    description="Transitions complaint through approved municipal workflow. Requires assigned department when moving to ASSIGNED.",
)
def patch_complaint_status(
    complaint_id: uuid.UUID,
    payload: AdminStatusTransitionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return transition_complaint_status(
        db=db,
        complaint_id=complaint_id,
        new_status=payload.status,
        admin=current_user,
        department_id=payload.department_id,
        remark=payload.remark,
    )


@router.post(
    "/complaints/{complaint_id}/remarks",
    response_model=AdminComplaintDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add official progress remark",
    description="Appends an official progress note to the complaint audit trail.",
)
def post_complaint_remark(
    complaint_id: uuid.UUID,
    payload: AdminProgressRemarkRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return add_complaint_progress_remark(
        db=db,
        complaint_id=complaint_id,
        remark=payload.remark,
        admin=current_user,
    )


@router.get(
    "/departments",
    response_model=List[DepartmentResponse],
    summary="List active departments",
    description="Retrieves active departments for assignment filtering and selection.",
)
def list_departments(
    city_id: Optional[uuid.UUID] = Query(None, description="Filter by city ID"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    departments = get_departments(db=db, city_id=city_id)
    return [
        DepartmentResponse(
            id=d.id,
            city_id=d.city_id,
            name=d.name,
            description=d.description,
            is_active=d.is_active,
        )
        for d in departments
    ]
