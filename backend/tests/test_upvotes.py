import uuid
from decimal import Decimal
import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.city import City
from app.models.complaint import Complaint
from app.models.enums import ComplaintCategory, ComplaintSeverity, ComplaintStatus, UserRole
from app.models.upvote import Upvote
from app.models.user import User
from app.services.jwt_service import create_access_token
from app.services.priority_service import (
    SEVERITY_WEIGHTS,
    calculate_priority_score,
    get_severity_weight,
)
from geoalchemy2 import WKTElement


def _get_auth_headers(user: User) -> dict:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(user_id=user.id, role=role_str)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_city(db_session: Session) -> City:
    city = db_session.scalar(select(City).where(City.name == "Vijayawada"))
    if not city:
        city = City(name="Vijayawada", state="Andhra Pradesh")
        db_session.add(city)
        db_session.flush()
    return city


@pytest.fixture
def citizen_a(db_session: Session, test_city: City) -> User:
    user = User(
        email="citizen.a@example.com",
        full_name="Citizen Alpha",
        role=UserRole.CITIZEN,
        city_id=test_city.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def citizen_b(db_session: Session, test_city: City) -> User:
    user = User(
        email="citizen.b@example.com",
        full_name="Citizen Beta",
        role=UserRole.CITIZEN,
        city_id=test_city.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session, test_city: City) -> User:
    user = User(
        email="admin.officer@example.com",
        full_name="Admin Officer",
        role=UserRole.ADMIN,
        city_id=test_city.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_complaint(db_session: Session, test_city: City, citizen_a: User) -> Complaint:
    complaint = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="Pothole on Main Road",
        description="Hazardous cavity in asphalt needing immediate attention.",
        category=ComplaintCategory.ROADS,
        severity=ComplaintSeverity.MEDIUM,
        status=ComplaintStatus.SUBMITTED,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="GPS",
    )
    db_session.add(complaint)
    db_session.commit()
    db_session.refresh(complaint)
    return complaint


# ===========================================================================
# A. Authentication Tests
# ===========================================================================

def test_a1_unauthenticated_cannot_upvote(auth_client, sample_complaint):
    """Unauthenticated requests must fail with 401."""
    res = auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote")
    assert res.status_code == 401


def test_a2_authenticated_citizen_can_upvote(auth_client, citizen_a, sample_complaint):
    """Authenticated citizen can upvote a valid complaint."""
    headers = _get_auth_headers(citizen_a)
    res = auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["complaint_id"] == str(sample_complaint.id)
    assert data["has_upvoted"] is True
    assert data["upvote_count"] == 1
    # MEDIUM (25) + 1 upvote = 26
    assert data["priority_score"] == 26


# ===========================================================================
# B. Authorization & IDOR Tests
# ===========================================================================

def test_b1_admin_cannot_use_citizen_upvote_endpoint(auth_client, admin_user, sample_complaint):
    """Admins are forbidden (403) from calling the citizen upvote endpoint."""
    headers = _get_auth_headers(admin_user)
    res = auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)
    assert res.status_code == 403


def test_b2_admin_cannot_delete_upvote_via_citizen_endpoint(auth_client, admin_user, sample_complaint):
    """Admins are forbidden (403) from calling citizen delete upvote endpoint."""
    headers = _get_auth_headers(admin_user)
    res = auth_client.delete(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)
    assert res.status_code == 403


def test_b3_cannot_upvote_nonexistent_complaint(auth_client, citizen_a):
    """Attempting to upvote a nonexistent complaint ID returns 404."""
    headers = _get_auth_headers(citizen_a)
    random_id = uuid.uuid4()
    res = auth_client.post(f"/api/v1/complaints/{random_id}/upvote", headers=headers)
    assert res.status_code == 404


# ===========================================================================
# C. Duplicate Prevention & Database Integrity Tests
# ===========================================================================

def test_c1_same_citizen_cannot_upvote_twice(auth_client, citizen_a, sample_complaint):
    """Same citizen upvoting twice receives 409 Conflict without count corruption."""
    headers = _get_auth_headers(citizen_a)

    # First vote succeeds
    res1 = auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["upvote_count"] == 1

    # Second vote returns 409 Conflict
    res2 = auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)
    assert res2.status_code == 409
    msg = res2.json().get("message") or res2.json().get("detail", "")
    assert "already upvoted" in msg.lower()

    # Count remains exactly 1
    status_res = auth_client.get(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["upvote_count"] == 1


def test_c2_database_unique_constraint_enforced(db_session, citizen_a, sample_complaint):
    """Verifies that DB level unique constraint blocks duplicates via IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    vote1 = Upvote(complaint_id=sample_complaint.id, user_id=citizen_a.id)
    db_session.add(vote1)
    db_session.commit()

    vote2 = Upvote(complaint_id=sample_complaint.id, user_id=citizen_a.id)
    db_session.add(vote2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ===========================================================================
# D. Upvote Removal Tests
# ===========================================================================

def test_d1_citizen_can_remove_own_upvote(auth_client, citizen_a, sample_complaint):
    """Citizen can rescind their own upvote; count and score decrement."""
    headers = _get_auth_headers(citizen_a)

    # Add upvote
    auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)

    # Remove upvote
    res = auth_client.delete(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_upvoted"] is False
    assert data["upvote_count"] == 0
    # MEDIUM (25) + 0 upvotes = 25
    assert data["priority_score"] == 25


def test_d2_removing_nonexistent_upvote_returns_404(auth_client, citizen_a, sample_complaint):
    """Attempting to remove an upvote when the citizen has not voted returns 404."""
    headers = _get_auth_headers(citizen_a)
    res = auth_client.delete(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)
    assert res.status_code == 404
    msg = res.json().get("message") or res.json().get("detail", "")
    assert "not upvoted" in msg.lower()


# ===========================================================================
# E. Citizen Isolation Tests
# ===========================================================================

def test_e1_citizen_vote_isolation(auth_client, citizen_a, citizen_b, sample_complaint):
    """
    Citizen A upvotes complaint.
    Citizen B checks status: has_upvoted = False, count = 1.
    Citizen B cannot remove A's vote.
    Citizen B creates own vote: count = 2.
    Both citizens see has_upvoted = True for themselves.
    """
    headers_a = _get_auth_headers(citizen_a)
    headers_b = _get_auth_headers(citizen_b)

    # Citizen A upvotes
    res_a = auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers_a)
    assert res_a.status_code == 200
    assert res_a.json()["upvote_count"] == 1

    # Citizen B views upvote status
    res_b_status = auth_client.get(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers_b)
    assert res_b_status.status_code == 200
    assert res_b_status.json()["has_upvoted"] is False
    assert res_b_status.json()["upvote_count"] == 1

    # Citizen B cannot remove A's vote (returns 404 for B)
    res_b_del = auth_client.delete(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers_b)
    assert res_b_del.status_code == 404

    # Citizen B casts their own vote
    res_b_vote = auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers_b)
    assert res_b_vote.status_code == 200
    assert res_b_vote.json()["has_upvoted"] is True
    assert res_b_vote.json()["upvote_count"] == 2
    # MEDIUM (25) + 2 upvotes = 27
    assert res_b_vote.json()["priority_score"] == 27

    # Citizen A also sees total count = 2 and their own has_upvoted = True
    res_a_check = auth_client.get(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers_a)
    assert res_a_check.json()["has_upvoted"] is True
    assert res_a_check.json()["upvote_count"] == 2


# ===========================================================================
# F. Priority Calculation Tests
# ===========================================================================

def test_f1_priority_calculation_formula():
    """Verifies calculate_priority_score for every severity level and upvote count."""
    # LOW (weight 10)
    assert calculate_priority_score(ComplaintSeverity.LOW, 0) == 10
    assert calculate_priority_score(ComplaintSeverity.LOW, 5) == 15
    assert calculate_priority_score("LOW", 0) == 10
    assert calculate_priority_score("LOW", 5) == 15

    # MEDIUM (weight 25)
    assert calculate_priority_score(ComplaintSeverity.MEDIUM, 0) == 25
    assert calculate_priority_score(ComplaintSeverity.MEDIUM, 20) == 45
    assert calculate_priority_score("MEDIUM", 0) == 25
    assert calculate_priority_score("MEDIUM", 20) == 45

    # HIGH (weight 50)
    assert calculate_priority_score(ComplaintSeverity.HIGH, 0) == 50
    assert calculate_priority_score(ComplaintSeverity.HIGH, 100) == 150
    assert calculate_priority_score("HIGH", 0) == 50
    assert calculate_priority_score("HIGH", 100) == 150

    # Negative / None edge case safety
    assert calculate_priority_score("HIGH", -5) == 50
    assert calculate_priority_score("HIGH", None) == 50


# ===========================================================================
# G. Community Sorting Tests
# ===========================================================================

def test_g1_community_sorting_higher_priority_first(auth_client, citizen_a, test_city, db_session):
    """
    Creates 3 complaints with different severities and upvotes:
    Complaint 1: LOW + 0 upvotes -> Priority 10
    Complaint 2: MEDIUM + 0 upvotes -> Priority 25
    Complaint 3: LOW + 20 upvotes -> Priority 30 (10 + 20)
    Expected Order in Community Feed: Complaint 3 (30) > Complaint 2 (25) > Complaint 1 (10).
    """
    headers = _get_auth_headers(citizen_a)

    c1 = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="Low priority issue",
        description="Minor crack on the footpath.",
        category=ComplaintCategory.ROADS,
        severity=ComplaintSeverity.LOW,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="MANUAL",
    )
    c2 = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="Medium priority issue",
        description="Flickering streetlight on the corner.",
        category=ComplaintCategory.STREETLIGHTS,
        severity=ComplaintSeverity.MEDIUM,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="MANUAL",
    )
    c3 = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="Low severity but many upvotes",
        description="Footpath issue that 20 citizens upvoted.",
        category=ComplaintCategory.ROADS,
        severity=ComplaintSeverity.LOW,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="MANUAL",
    )
    db_session.add_all([c1, c2, c3])
    db_session.commit()

    # Simulate 20 upvotes for c3
    for i in range(20):
        voter = User(
            email=f"voter_{i}@example.com",
            full_name=f"Voter {i}",
            role=UserRole.CITIZEN,
            city_id=test_city.id,
            is_active=True,
            is_verified=True,
        )
        db_session.add(voter)
        db_session.flush()
        upvote = Upvote(complaint_id=c3.id, user_id=voter.id)
        db_session.add(upvote)
    db_session.commit()

    # Fetch community complaints (mine_only=false)
    res = auth_client.get("/api/v1/complaints?mine_only=false", headers=headers)
    assert res.status_code == 200
    items = res.json()

    # Filter to our 3 complaints
    test_items = [item for item in items if item["id"] in [str(c1.id), str(c2.id), str(c3.id)]]
    assert len(test_items) == 3

    assert test_items[0]["id"] == str(c3.id)
    assert test_items[0]["priority_score"] == 30

    assert test_items[1]["id"] == str(c2.id)
    assert test_items[1]["priority_score"] == 25

    assert test_items[2]["id"] == str(c1.id)
    assert test_items[2]["priority_score"] == 10


def test_g2_community_sorting_tiebreaker_newer_first(auth_client, citizen_a, test_city, db_session):
    """
    Creates 2 complaints with equal priority score (both HIGH, 0 upvotes -> Priority 50).
    Verifies that the newer created_at complaint appears first.
    """
    from datetime import datetime, timezone, timedelta

    headers = _get_auth_headers(citizen_a)
    now = datetime.now(timezone.utc)

    c_older = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="Older High priority issue",
        description="Severe pipeline leak.",
        category=ComplaintCategory.WATER,
        severity=ComplaintSeverity.HIGH,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="MANUAL",
        created_at=now - timedelta(hours=2),
    )
    c_newer = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="Newer High priority issue",
        description="Hazardous live electrical wire.",
        category=ComplaintCategory.PUBLIC_SAFETY,
        severity=ComplaintSeverity.HIGH,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="MANUAL",
        created_at=now,
    )
    db_session.add_all([c_older, c_newer])
    db_session.commit()

    res = auth_client.get("/api/v1/complaints?mine_only=false", headers=headers)
    assert res.status_code == 200
    items = res.json()

    test_items = [item for item in items if item["id"] in [str(c_older.id), str(c_newer.id)]]
    assert len(test_items) == 2

    # Both have priority 50
    assert test_items[0]["priority_score"] == 50
    assert test_items[1]["priority_score"] == 50

    # Newer must appear before older
    assert test_items[0]["id"] == str(c_newer.id)
    assert test_items[1]["id"] == str(c_older.id)


def test_h1_complaint_detail_exposes_upvote_and_priority(auth_client, citizen_a, sample_complaint):
    """Verifies complaint detail endpoint returns upvote_count, has_upvoted, and priority_score."""
    headers = _get_auth_headers(citizen_a)

    # Initial detail check before voting
    res1 = auth_client.get(f"/api/v1/complaints/{sample_complaint.id}", headers=headers)
    assert res1.status_code == 200
    body1 = res1.json()
    assert body1["upvote_count"] == 0
    assert body1["has_upvoted"] is False
    assert body1["priority_score"] == 25  # MEDIUM = 25

    # Citizen upvotes
    auth_client.post(f"/api/v1/complaints/{sample_complaint.id}/upvote", headers=headers)

    # Detail check after voting
    res2 = auth_client.get(f"/api/v1/complaints/{sample_complaint.id}", headers=headers)
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["upvote_count"] == 1
    assert body2["has_upvoted"] is True
    assert body2["priority_score"] == 26
