import uuid
from datetime import datetime, timezone, timedelta
import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import select

from app.models.city import City
from app.models.complaint import Complaint
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
from app.services.jwt_service import create_access_token


def _get_auth_headers(user: User) -> dict:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(user_id=user.id, role=role_str)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_city(db_session) -> City:
    city = db_session.scalar(select(City).where(City.name == "Vijayawada"))
    if not city:
        city = City(name="Vijayawada", state="Andhra Pradesh")
        db_session.add(city)
        db_session.flush()
    return city


@pytest.fixture
def citizen_a(db_session, test_city) -> User:
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
def admin_user(db_session, test_city):
    admin = User(
        email="admin_ops@example.com",
        full_name="Municipal Admin",
        role=UserRole.ADMIN,
        city_id=test_city.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_department(db_session, test_city):
    dept = Department(
        city_id=test_city.id,
        name="Roads & Infrastructure",
        description="Handles road repairs and pavement",
        is_active=True,
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


@pytest.fixture
def other_city_department(db_session):
    other_city = City(
        name="Hyderabad",
        state="Telangana",
        country="India",
        is_active=True,
    )
    db_session.add(other_city)
    db_session.flush()

    dept = Department(
        city_id=other_city.id,
        name="GHMC Roads",
        is_active=True,
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


@pytest.fixture
def base_complaint(db_session, citizen_a, test_city):
    complaint = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="Pothole on Main Road",
        description="Dangerous large pothole near the central bus terminal.",
        category=ComplaintCategory.ROADS,
        severity=ComplaintSeverity.LOW,
        status=ComplaintStatus.SUBMITTED,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="MANUAL",
    )
    db_session.add(complaint)
    db_session.flush()

    # Initial audit update
    initial_upd = ComplaintUpdate(
        complaint_id=complaint.id,
        updated_by_user_id=citizen_a.id,
        action_type=ComplaintActionType.STATUS_CHANGE,
        old_status=None,
        new_status=ComplaintStatus.SUBMITTED,
        remark="Initial report filed",
        progress_percentage=0,
    )
    db_session.add(initial_upd)
    db_session.commit()
    db_session.refresh(complaint)
    return complaint


# ============================================================================
# 1. Authorization Boundaries
# ============================================================================

def test_a1_unauthenticated_cannot_access_admin_endpoints(client, base_complaint):
    # Dashboard
    res = client.get("/api/v1/admin/dashboard")
    assert res.status_code == 401

    # Complaints list
    res = client.get("/api/v1/admin/complaints")
    assert res.status_code == 401

    # Detail
    res = client.get(f"/api/v1/admin/complaints/{base_complaint.id}")
    assert res.status_code == 401

    # Severity patch
    res = client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/severity",
        json={"severity": "HIGH"},
    )
    assert res.status_code == 401


def test_a2_citizen_cannot_access_admin_dashboard(auth_client, citizen_a):
    headers = _get_auth_headers(citizen_a)
    res = auth_client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 403


def test_a3_citizen_cannot_access_admin_complaint_list(auth_client, citizen_a):
    headers = _get_auth_headers(citizen_a)
    res = auth_client.get("/api/v1/admin/complaints", headers=headers)
    assert res.status_code == 403


def test_a4_citizen_cannot_update_severity(auth_client, citizen_a, base_complaint):
    headers = _get_auth_headers(citizen_a)
    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/severity",
        headers=headers,
        json={"severity": "HIGH"},
    )
    assert res.status_code == 403


def test_a5_citizen_cannot_assign_department(auth_client, citizen_a, base_complaint, test_department):
    headers = _get_auth_headers(citizen_a)
    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/department",
        headers=headers,
        json={"department_id": str(test_department.id)},
    )
    assert res.status_code == 403


def test_a6_citizen_cannot_transition_status(auth_client, citizen_a, base_complaint):
    headers = _get_auth_headers(citizen_a)
    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "UNDER_REVIEW"},
    )
    assert res.status_code == 403


def test_a7_citizen_cannot_add_progress_remark(auth_client, citizen_a, base_complaint):
    headers = _get_auth_headers(citizen_a)
    res = auth_client.post(
        f"/api/v1/admin/complaints/{base_complaint.id}/remarks",
        headers=headers,
        json={"remark": "Citizen comment attempt"},
    )
    assert res.status_code == 403


# ============================================================================
# 2. Admin Operational Dashboard
# ============================================================================

def test_b1_admin_dashboard_returns_real_aggregates(auth_client, admin_user, base_complaint):
    headers = _get_auth_headers(admin_user)
    res = auth_client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_complaints"] >= 1
    assert data["submitted_count"] >= 1
    assert data["under_review_count"] == 0
    assert data["assigned_count"] == 0
    assert data["in_progress_count"] == 0
    assert data["resolved_count"] == 0
    assert data["rejected_count"] == 0
    assert data["low_severity_count"] >= 1
    assert data["unassigned_count"] >= 1
    assert isinstance(data["recent_priority_complaints"], list)


# ============================================================================
# 3. Complaint Queue, Priority Sorting, Search & Filtering
# ============================================================================

def test_c1_admin_complaints_ordered_by_priority_score(auth_client, admin_user, citizen_a, test_city, db_session):
    headers = _get_auth_headers(admin_user)

    # c_low: LOW (10) + 0 = 10
    c_low = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="Low Priority Queue Item",
        description="Faded paint on curb.",
        category=ComplaintCategory.ROADS,
        severity=ComplaintSeverity.LOW,
        status=ComplaintStatus.SUBMITTED,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="MANUAL",
    )
    # c_high: HIGH (50) + 0 = 50
    c_high = Complaint(
        city_id=test_city.id,
        user_id=citizen_a.id,
        title="High Priority Queue Item",
        description="Open manhole on footpath.",
        category=ComplaintCategory.DRAINAGE,
        severity=ComplaintSeverity.HIGH,
        status=ComplaintStatus.SUBMITTED,
        location=WKTElement("POINT(80.648 16.506)", srid=4326),
        location_source="MANUAL",
    )
    db_session.add_all([c_low, c_high])
    db_session.commit()

    res = auth_client.get("/api/v1/admin/complaints", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]

    item_ids = [item["id"] for item in items]
    assert str(c_high.id) in item_ids
    assert str(c_low.id) in item_ids

    # c_high must appear before c_low
    assert item_ids.index(str(c_high.id)) < item_ids.index(str(c_low.id))


def test_c2_admin_complaints_search_and_filters(auth_client, admin_user, base_complaint, test_department, db_session):
    headers = _get_auth_headers(admin_user)

    # Search by title
    res = auth_client.get("/api/v1/admin/complaints?search=Pothole", headers=headers)
    assert res.status_code == 200
    assert any(item["id"] == str(base_complaint.id) for item in res.json()["items"])

    # Search by ID
    res = auth_client.get(f"/api/v1/admin/complaints?search={str(base_complaint.id)[:8]}", headers=headers)
    assert res.status_code == 200
    assert any(item["id"] == str(base_complaint.id) for item in res.json()["items"])

    # Filter by category
    res = auth_client.get("/api/v1/admin/complaints?category=ROADS", headers=headers)
    assert res.status_code == 200
    assert any(item["id"] == str(base_complaint.id) for item in res.json()["items"])

    res_other = auth_client.get("/api/v1/admin/complaints?category=WATER", headers=headers)
    assert res_other.status_code == 200
    assert not any(item["id"] == str(base_complaint.id) for item in res_other.json()["items"])


# ============================================================================
# 4. Severity Management
# ============================================================================

def test_d1_admin_can_update_severity_and_priority_recalculates(auth_client, admin_user, base_complaint, db_session):
    headers = _get_auth_headers(admin_user)

    # Initially LOW: severity_weight = 10, priority_score = 10
    assert base_complaint.severity == ComplaintSeverity.LOW

    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/severity",
        headers=headers,
        json={"severity": "HIGH", "remark": "Escalated after field inspection"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["severity"] == "HIGH"
    assert data["severity_weight"] == 50
    assert data["priority_score"] == 50  # 50 + 0 upvotes

    # Verify structured audit log entry created
    last_update = data["updates"][-1]
    assert last_update["action_type"] == "SEVERITY_CHANGE"
    assert last_update["old_severity"] == "LOW"
    assert last_update["new_severity"] == "HIGH"
    assert "Escalated" in last_update["remark"]
    assert "Admin" in last_update["actor_label"]


def test_d2_admin_update_severity_critical_rejected(auth_client, admin_user, base_complaint):
    headers = _get_auth_headers(admin_user)
    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/severity",
        headers=headers,
        json={"severity": "CRITICAL"},
    )
    assert res.status_code == 422


# ============================================================================
# 5. Department Assignment & Multi-City Validation
# ============================================================================

def test_e1_admin_can_assign_valid_department_in_same_city(auth_client, admin_user, base_complaint, test_department):
    headers = _get_auth_headers(admin_user)

    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/department",
        headers=headers,
        json={"department_id": str(test_department.id), "remark": "Assigned to Roads team"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["department_id"] == str(test_department.id)
    assert data["department_name"] == test_department.name

    # Check structured audit entry
    last_update = data["updates"][-1]
    assert last_update["action_type"] == "DEPARTMENT_ASSIGNMENT"
    assert last_update["old_department_id"] is None
    assert last_update["new_department_id"] == str(test_department.id)


def test_e2_admin_cannot_assign_department_from_different_city(auth_client, admin_user, base_complaint, other_city_department):
    headers = _get_auth_headers(admin_user)

    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/department",
        headers=headers,
        json={"department_id": str(other_city_department.id)},
    )
    assert res.status_code == 400
    msg = (res.json().get("message") or res.json().get("detail") or "").lower()
    assert "different city" in msg


def test_e3_admin_can_unassign_department(auth_client, admin_user, base_complaint, test_department):
    headers = _get_auth_headers(admin_user)

    # First assign
    auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/department",
        headers=headers,
        json={"department_id": str(test_department.id)},
    )

    # Now unassign
    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/department",
        headers=headers,
        json={"department_id": None, "remark": "Removed assignment for reassessment"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["department_id"] is None
    assert data["department_name"] is None

    last_update = data["updates"][-1]
    assert last_update["action_type"] == "DEPARTMENT_ASSIGNMENT"
    assert last_update["old_department_id"] == str(test_department.id)
    assert last_update["new_department_id"] is None


# ============================================================================
# 6. Lifecycle Transitions & State Machine Invariants
# ============================================================================

def test_f1_valid_lifecycle_transitions(auth_client, admin_user, base_complaint, test_department):
    headers = _get_auth_headers(admin_user)

    # 1. SUBMITTED -> UNDER_REVIEW (25%)
    res1 = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "UNDER_REVIEW", "remark": "Complaint under initial review"},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "UNDER_REVIEW"
    assert res1.json()["updates"][-1]["progress_percentage"] == 25

    # 2. UNDER_REVIEW -> ASSIGNED (50%) with atomic department assignment
    res2 = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={
            "status": "ASSIGNED",
            "department_id": str(test_department.id),
            "remark": "Assigned to road maintenance division",
        },
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "ASSIGNED"
    assert res2.json()["department_id"] == str(test_department.id)
    assert res2.json()["updates"][-1]["progress_percentage"] == 50
    assert res2.json()["updates"][-1]["new_department_id"] == str(test_department.id)

    # 3. ASSIGNED -> IN_PROGRESS (75%)
    res3 = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "IN_PROGRESS", "remark": "Field crew dispatched"},
    )
    assert res3.status_code == 200
    assert res3.json()["status"] == "IN_PROGRESS"
    assert res3.json()["updates"][-1]["progress_percentage"] == 75

    # 4. IN_PROGRESS -> RESOLVED (100%)
    res4 = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "RESOLVED", "remark": "Pothole filled and road surface restored"},
    )
    assert res4.status_code == 200
    assert res4.json()["status"] == "RESOLVED"
    assert res4.json()["updates"][-1]["progress_percentage"] == 100


def test_f2_transition_under_review_to_rejected(auth_client, admin_user, base_complaint):
    headers = _get_auth_headers(admin_user)

    # Move to UNDER_REVIEW
    auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "UNDER_REVIEW"},
    )

    # Move to REJECTED
    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "REJECTED", "remark": "Private property issue, not municipal jurisdiction"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"
    assert res.json()["updates"][-1]["progress_percentage"] == 0


def test_f3_transition_to_assigned_requires_department(auth_client, admin_user, base_complaint):
    headers = _get_auth_headers(admin_user)

    # Move to UNDER_REVIEW
    auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "UNDER_REVIEW"},
    )

    # Try ASSIGNED without department
    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "ASSIGNED"},
    )
    assert res.status_code == 400
    msg = (res.json().get("message") or res.json().get("detail") or "").lower()
    assert "assigned department" in msg


def test_f4_invalid_lifecycle_transitions_rejected(auth_client, admin_user, base_complaint):
    headers = _get_auth_headers(admin_user)

    # SUBMITTED -> RESOLVED is invalid
    res = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "RESOLVED"},
    )
    assert res.status_code == 400

    # SUBMITTED -> IN_PROGRESS is invalid
    res2 = auth_client.patch(
        f"/api/v1/admin/complaints/{base_complaint.id}/status",
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )
    assert res2.status_code == 400


# ============================================================================
# 7. Progress Remarks
# ============================================================================

def test_g1_admin_can_add_progress_remark(auth_client, admin_user, base_complaint):
    headers = _get_auth_headers(admin_user)

    res = auth_client.post(
        f"/api/v1/admin/complaints/{base_complaint.id}/remarks",
        headers=headers,
        json={"remark": "Site inspection scheduled for tomorrow morning."},
    )
    assert res.status_code == 201
    data = res.json()

    last_update = data["updates"][-1]
    assert last_update["action_type"] == "PROGRESS_REMARK"
    assert "Site inspection scheduled" in last_update["remark"]
    assert "Admin" in last_update["actor_label"]


def test_g2_admin_progress_remark_too_short_rejected(auth_client, admin_user, base_complaint):
    headers = _get_auth_headers(admin_user)

    res = auth_client.post(
        f"/api/v1/admin/complaints/{base_complaint.id}/remarks",
        headers=headers,
        json={"remark": "hi"},
    )
    assert res.status_code in [400, 422]


# ============================================================================
# 8. Department List Endpoint
# ============================================================================

def test_h1_admin_can_list_departments(auth_client, admin_user, test_department, test_city):
    headers = _get_auth_headers(admin_user)

    res = auth_client.get("/api/v1/admin/departments", headers=headers)
    assert res.status_code == 200
    depts = res.json()
    assert any(d["id"] == str(test_department.id) for d in depts)

    res_city = auth_client.get(f"/api/v1/admin/departments?city_id={test_city.id}", headers=headers)
    assert res_city.status_code == 200
    depts_city = res_city.json()
    assert any(d["id"] == str(test_department.id) for d in depts_city)
