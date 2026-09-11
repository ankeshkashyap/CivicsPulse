import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ComplaintCategory, ComplaintSeverity, ComplaintStatus
from app.schemas.complaint import ComplaintImageResponse, ComplaintUpdateResponse


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    city_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool


class AdminComplaintListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    category: ComplaintCategory
    severity: ComplaintSeverity
    status: ComplaintStatus
    city_id: uuid.UUID
    city_name: str
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    latitude: float
    longitude: float
    location_source: str
    image_count: int = 0
    thumbnail_url: Optional[str] = None
    upvote_count: int = 0
    priority_score: int = 0
    created_at: datetime
    updated_at: datetime


class AdminComplaintListResponse(BaseModel):
    items: List[AdminComplaintListItemResponse]
    total: int
    limit: int
    offset: int


class AdminDashboardStatsResponse(BaseModel):
    total_complaints: int
    submitted_count: int
    under_review_count: int
    assigned_count: int
    in_progress_count: int
    resolved_count: int
    rejected_count: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    high_priority_count: int
    unassigned_count: int
    recent_priority_complaints: List[AdminComplaintListItemResponse]


class AdminComplaintDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    category: ComplaintCategory
    severity: ComplaintSeverity
    status: ComplaintStatus
    city_id: uuid.UUID
    city_name: str
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    latitude: float
    longitude: float
    location_source: str
    created_at: datetime
    updated_at: datetime
    images: List[ComplaintImageResponse]
    updates: List[ComplaintUpdateResponse]
    upvote_count: int = 0
    priority_score: int = 0
    severity_weight: int = 0


class AdminSeverityUpdateRequest(BaseModel):
    severity: ComplaintSeverity
    remark: Optional[str] = Field(None, max_length=1000)


class AdminDepartmentAssignRequest(BaseModel):
    department_id: Optional[uuid.UUID] = None
    remark: Optional[str] = Field(None, max_length=1000)


class AdminStatusTransitionRequest(BaseModel):
    status: ComplaintStatus
    department_id: Optional[uuid.UUID] = None
    remark: Optional[str] = Field(None, max_length=1000)


class AdminProgressRemarkRequest(BaseModel):
    remark: str = Field(..., min_length=3, max_length=1000)
