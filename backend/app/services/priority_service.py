"""
CivicPulse Deterministic Priority Scoring Service.

Computes complaint priority score based on upvote count and severity weight:
    priority_score = upvote_count + severity_weight

Severity weights:
    LOW = 10
    MEDIUM = 25
    HIGH = 50

Examples:
    LOW + 0 upvotes = 10
    LOW + 5 upvotes = 15
    MEDIUM + 0 upvotes = 25
    MEDIUM + 20 upvotes = 45
    HIGH + 0 upvotes = 50
    HIGH + 100 upvotes = 150
"""

from typing import Union
from sqlalchemy import case, ColumnElement
from app.models.enums import ComplaintSeverity

SEVERITY_WEIGHTS: dict[ComplaintSeverity, int] = {
    ComplaintSeverity.LOW: 10,
    ComplaintSeverity.MEDIUM: 25,
    ComplaintSeverity.HIGH: 50,
}


def get_severity_weight(severity: Union[ComplaintSeverity, str]) -> int:
    """Returns the integer priority weight for a given severity level."""
    if isinstance(severity, str):
        try:
            severity = ComplaintSeverity(severity)
        except ValueError:
            return 0
    return SEVERITY_WEIGHTS.get(severity, 0)


def calculate_priority_score(severity: Union[ComplaintSeverity, str], upvote_count: int) -> int:
    """
    Authoritative deterministic priority calculation function.
    Guarantees no duplicated formula implementations across the codebase.
    """
    count = max(0, int(upvote_count or 0))
    weight = get_severity_weight(severity)
    return count + weight


def get_severity_weight_sql(severity_column) -> ColumnElement[int]:
    """
    SQLAlchemy CASE construct mapping Complaint.severity to integer weight
    for database-level aggregation and deterministic ordering without N+1 queries.
    """
    return case(
        (severity_column == ComplaintSeverity.LOW, 10),
        (severity_column == ComplaintSeverity.MEDIUM, 25),
        (severity_column == ComplaintSeverity.HIGH, 50),
        else_=0,
    )
