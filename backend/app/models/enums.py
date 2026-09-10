from enum import Enum


class UserRole(str, Enum):
    CITIZEN = "CITIZEN"
    ADMIN = "ADMIN"


class ComplaintCategory(str, Enum):
    ROADS = "ROADS"
    STREETLIGHTS = "STREETLIGHTS"
    GARBAGE = "GARBAGE"
    DRAINAGE = "DRAINAGE"
    WATER = "WATER"
    SEWERAGE = "SEWERAGE"
    TRAFFIC = "TRAFFIC"
    PUBLIC_SAFETY = "PUBLIC_SAFETY"
    PARKS = "PARKS"
    OTHER = "OTHER"


class ComplaintSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ComplaintStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"