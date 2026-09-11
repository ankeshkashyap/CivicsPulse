import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ComplaintActionType, ComplaintCategory, ComplaintSeverity, ComplaintStatus


class ComplaintImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str
    public_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime


class ComplaintUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action_type: ComplaintActionType = ComplaintActionType.STATUS_CHANGE
    old_status: Optional[ComplaintStatus] = None
    new_status: ComplaintStatus
    old_severity: Optional[ComplaintSeverity] = None
    new_severity: Optional[ComplaintSeverity] = None
    old_department_id: Optional[uuid.UUID] = None
    old_department_name: Optional[str] = None
    new_department_id: Optional[uuid.UUID] = None
    new_department_name: Optional[str] = None
    remark: Optional[str] = None
    progress_percentage: int
    actor_role: str
    actor_label: str
    created_at: datetime



class ComplaintDetailResponse(BaseModel):
    """
    Comprehensive complaint view.
    Derived latitude and longitude are extracted from the canonical PostGIS POINT.
    Citizen identity is strictly isolated and sanitized for privacy.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    category: ComplaintCategory
    severity: ComplaintSeverity
    status: ComplaintStatus
    latitude: float
    longitude: float
    location_source: str
    city_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    images: List[ComplaintImageResponse]
    updates: List[ComplaintUpdateResponse]
    is_owner: bool = False
    upvote_count: int = 0
    has_upvoted: bool = False
    priority_score: int = 0


class ComplaintListItemResponse(BaseModel):
    """
    Sanitized summary representation suitable for community feeds and citizen rosters.
    Strictly excludes user_id, reporter email, and private metadata.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    category: ComplaintCategory
    severity: ComplaintSeverity
    status: ComplaintStatus
    latitude: float
    longitude: float
    location_source: str
    created_at: datetime
    preview_image_url: Optional[str] = None
    images_count: int = 0
    upvotes_count: int = 0
    has_upvoted: bool = False
    priority_score: int = 0
    is_owner: bool = False


class UpvoteResponse(BaseModel):
    complaint_id: uuid.UUID
    has_upvoted: bool
    upvote_count: int
    priority_score: int


class CitizenDashboardStatsResponse(BaseModel):
    """Real aggregate metrics for the authenticated citizen's personal dashboard."""
    total_submitted: int
    in_progress: int
    resolved: int
    rejected: int
    community_upvotes: int = 0
    recent_complaints: List[ComplaintListItemResponse]
