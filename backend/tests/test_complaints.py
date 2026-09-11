import io
import uuid
from decimal import Decimal
import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.city import City
from app.models.complaint import Complaint
from app.models.complaint_image import ComplaintImage
from app.models.complaint_update import ComplaintUpdate
from app.models.enums import ComplaintCategory, ComplaintSeverity, ComplaintStatus, UserRole
from app.models.user import User
from app.services.jwt_service import create_access_token
from app.services.image_storage import (
    ImageStorageProvider,
    StoredImageResult,
    get_image_storage_provider,
    set_image_storage_provider,
    MockImageStorageProvider,
)


def _get_auth_headers(user: User) -> dict:
    """Generates an Authorization header with a valid access token for the given user."""
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(user_id=user.id, role=role_str)
    return {"Authorization": f"Bearer {token}"}



@pytest.fixture
def citizen_user(db_session: Session) -> User:
    city = db_session.scalar(select(City).where(City.name == "Vijayawada"))
    if not city:
        city = City(name="Vijayawada", state="Andhra Pradesh")
        db_session.add(city)
        db_session.flush()

    user = User(
        email="citizen.reporter@example.com",
        full_name="Ravi Kumar",
        role=UserRole.CITIZEN,
        city_id=city.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_citizen_user(db_session: Session) -> User:
    city = db_session.scalar(select(City).where(City.name == "Vijayawada"))
    if not city:
        city = City(name="Vijayawada", state="Andhra Pradesh")
        db_session.add(city)
        db_session.flush()
    user = User(
        email="other.citizen@example.com",
        full_name="Priya Sharma",
        role=UserRole.CITIZEN,
        city_id=city.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    city = db_session.scalar(select(City).where(City.name == "Vijayawada"))
    if not city:
        city = City(name="Vijayawada", state="Andhra Pradesh")
        db_session.add(city)
        db_session.flush()
    user = User(
        email="admin.officer@civicpulse.org",
        full_name="Municipal Officer",
        role=UserRole.ADMIN,
        city_id=city.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_01_citizen_can_create_complaint(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 1: Authenticated citizen can create complaint with valid data and image."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("pothole.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Severe pothole near Benz Circle",
        "description": "Deep asphalt cavity in the northbound lane causing vehicle damage.",
        "category": "ROADS",
        "severity": "HIGH",
        "latitude": 16.506174,
        "longitude": 80.648015,
        "location_source": "GPS",
    }

    response = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert response.status_code == 201
    body = response.json()

    assert body["title"] == data["title"]
    assert body["description"] == data["description"]
    assert body["category"] == "ROADS"
    assert body["severity"] == "HIGH"
    assert body["status"] == "SUBMITTED"
    assert body["latitude"] == pytest.approx(16.506174, abs=1e-5)
    assert body["longitude"] == pytest.approx(80.648015, abs=1e-5)
    assert body["location_source"] == "GPS"
    assert len(body["images"]) == 1
    assert "civicpulse/complaints" in body["images"][0]["public_id"]
    assert body["is_owner"] is True


def test_02_unauthenticated_user_cannot_create_complaint(auth_client, sample_jpeg_bytes):
    """Test 2: Unauthenticated request to create complaint is rejected with 401."""
    files = [("images", ("pothole.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Severe pothole near Benz Circle",
        "description": "Deep cavity in the roadway.",
        "category": "ROADS",
        "latitude": 16.506174,
        "longitude": 80.648015,
    }

    response = auth_client.post("/api/v1/complaints", data=data, files=files)
    assert response.status_code == 401


def test_03_invalid_title_rejected(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 3: Title must be between 5 and 200 characters and not whitespace-only."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("pothole.jpg", sample_jpeg_bytes, "image/jpeg"))]

    # Too short (< 5 chars)
    data_short = {
        "title": "Poth",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data_short, files=files, headers=headers)
    assert res.status_code == 422

    # Whitespace only
    data_whitespace = {
        "title": "     ",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data_whitespace, files=files, headers=headers)
    assert res.status_code == 422

    # Too long (> 200 chars)
    data_long = {
        "title": "A" * 201,
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data_long, files=files, headers=headers)
    assert res.status_code == 422


def test_04_invalid_description_rejected(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 4: Description must be between 10 and 5000 characters."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("pothole.jpg", sample_jpeg_bytes, "image/jpeg"))]

    # Too short (< 10 chars)
    data_short = {
        "title": "Valid Title Here",
        "description": "Too short",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data_short, files=files, headers=headers)
    assert res.status_code == 422

    # Too long (> 5000 chars)
    data_long = {
        "title": "Valid Title Here",
        "description": "B" * 5001,
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data_long, files=files, headers=headers)
    assert res.status_code == 422


def test_05_invalid_category_rejected(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 5: Invalid category is rejected."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("pothole.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Valid Title Here",
        "description": "Valid description of the issue here.",
        "category": "NON_EXISTENT_CATEGORY",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 422


def test_06_invalid_severity_rejected(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 6: Invalid severity is rejected."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("pothole.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Valid Title Here",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "severity": "CRITICAL_INVALID",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 422


def test_07_invalid_coordinates_rejected(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 7: Coordinates outside valid ranges are rejected."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("pothole.jpg", sample_jpeg_bytes, "image/jpeg"))]

    # Latitude out of range (> 90)
    data_bad_lat = {
        "title": "Valid Title Here",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 95.0,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data_bad_lat, files=files, headers=headers)
    assert res.status_code == 422

    # Longitude out of range (< -180)
    data_bad_lon = {
        "title": "Valid Title Here",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": -190.0,
    }
    res = auth_client.post("/api/v1/complaints", data=data_bad_lon, files=files, headers=headers)
    assert res.status_code == 422


def test_08_missing_image_rejected(auth_client, citizen_user):
    """Test 8: Request without any evidence images is rejected."""
    headers = _get_auth_headers(citizen_user)
    data = {
        "title": "Valid Title Here",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    # No files attached
    res = auth_client.post("/api/v1/complaints", data=data, files=[], headers=headers)
    assert res.status_code == 422


def test_09_more_than_three_images_rejected(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 9: Attaching more than 3 images is rejected."""
    headers = _get_auth_headers(citizen_user)
    files = [
        ("images", ("img1.jpg", sample_jpeg_bytes, "image/jpeg")),
        ("images", ("img2.jpg", sample_jpeg_bytes, "image/jpeg")),
        ("images", ("img3.jpg", sample_jpeg_bytes, "image/jpeg")),
        ("images", ("img4.jpg", sample_jpeg_bytes, "image/jpeg")),
    ]
    data = {
        "title": "Valid Title Here",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 422
    msg = res.json().get("message") or res.json().get("detail", "")
    assert "maximum of 3" in msg.lower()


def test_10_unsupported_file_type_rejected(auth_client, citizen_user):
    """Test 10: Non-image or unsupported format is rejected."""
    headers = _get_auth_headers(citizen_user)
    fake_txt_bytes = b"This is a text file, not an image."
    files = [("images", ("notes.txt", fake_txt_bytes, "text/plain"))]
    data = {
        "title": "Valid Title Here",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 422
    msg = res.json().get("message") or res.json().get("detail", "")
    assert "unsupported image format" in msg.lower()


def test_11_oversized_image_rejected(auth_client, citizen_user):
    """Test 11: Image exceeding 5MB is rejected."""
    headers = _get_auth_headers(citizen_user)
    oversized_bytes = b"\xff\xd8\xff" + b"0" * (6 * 1024 * 1024)
    files = [("images", ("large.jpg", oversized_bytes, "image/jpeg"))]
    data = {
        "title": "Valid Title Here",
        "description": "Valid description of the issue here.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 422
    msg = res.json().get("message") or res.json().get("detail", "")
    assert "exceeds the maximum" in msg.lower()


def test_12_complaint_starts_as_submitted(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 12: Created complaint strictly starts in SUBMITTED state."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Streetlight unlit on Ring Road",
        "description": "Pole fixture 42 has been dark for two consecutive nights.",
        "category": "STREETLIGHTS",
        "latitude": 16.510000,
        "longitude": 80.640000,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 201
    assert res.json()["status"] == "SUBMITTED"


def test_13_initial_complaint_update_created(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 13: Initial ComplaintUpdate audit record is automatically logged with status SUBMITTED."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Clogged storm drain",
        "description": "Storm drain backing up water during light showers.",
        "category": "DRAINAGE",
        "latitude": 16.512000,
        "longitude": 80.641000,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 201
    updates = res.json()["updates"]
    assert len(updates) == 1
    assert updates[0]["new_status"] == "SUBMITTED"
    assert updates[0]["old_status"] is None
    assert updates[0]["progress_percentage"] == 0
    assert "actor_role" in updates[0]
    assert updates[0]["actor_role"] == "CITIZEN"


def test_14_complaint_belongs_to_authenticated_citizen(auth_client, citizen_user, sample_jpeg_bytes, db_session):
    """Test 14: Complaint user_id matches authenticated citizen."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Accumulated garbage",
        "description": "Waste overflowing on pedestrian footpath.",
        "category": "GARBAGE",
        "latitude": 16.505000,
        "longitude": 80.642000,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    complaint_id = uuid.UUID(res.json()["id"])

    db_complaint = db_session.scalar(select(Complaint).where(Complaint.id == complaint_id))
    assert db_complaint.user_id == citizen_user.id


def test_15_citizen_cannot_see_private_identity_in_community_list(auth_client, citizen_user, other_citizen_user, sample_jpeg_bytes):
    """Test 15: Public/community list strips private user details (no email, user_id, or auth data)."""
    # Create complaint as citizen_user
    headers_author = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Public park bench broken",
        "description": "Wooden slat shattered at municipal park.",
        "category": "PARKS",
        "latitude": 16.504000,
        "longitude": 80.643000,
    }
    auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers_author)

    # Read as other_citizen_user
    headers_reader = _get_auth_headers(other_citizen_user)
    res = auth_client.get("/api/v1/complaints", headers=headers_reader)
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1

    for item in items:
        # Verify strict privacy isolation
        assert "user_id" not in item
        assert "email" not in item
        assert "user" not in item
        assert "token" not in item


def test_16_client_cannot_change_status_through_create_endpoint(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 16: Client cannot pass status='RESOLVED' to bypass triage."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Attempted status override",
        "description": "Citizen trying to submit pre-resolved issue.",
        "category": "ROADS",
        "status": "RESOLVED",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 201
    # Backend overrides and forces SUBMITTED
    assert res.json()["status"] == "SUBMITTED"


def test_17_client_cannot_assign_department_through_create_endpoint(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 17: Client cannot assign department_id through create endpoint."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    random_dept_id = str(uuid.uuid4())
    data = {
        "title": "Attempted department assign",
        "description": "Citizen trying to assign department directly.",
        "category": "ROADS",
        "department_id": random_dept_id,
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 201
    assert res.json()["department_id"] is None


def test_18_complaint_detail_works(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 18: Complaint detail endpoint returns full record, images, and history."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Water pipeline leakage",
        "description": "Clean potable water leaking onto street surface.",
        "category": "WATER",
        "latitude": 16.513000,
        "longitude": 80.646000,
    }
    create_res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    complaint_id = create_res.json()["id"]

    detail_res = auth_client.get(f"/api/v1/complaints/{complaint_id}", headers=headers)
    assert detail_res.status_code == 200
    body = detail_res.json()
    assert body["id"] == complaint_id
    assert body["title"] == data["title"]
    assert len(body["images"]) == 1
    assert len(body["updates"]) == 1


def test_19_complaint_history_is_chronological(auth_client, citizen_user, admin_user, sample_jpeg_bytes, db_session):
    """Test 19: History updates are strictly ordered by created_at asc."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Chronological audit test",
        "description": "Checking update order in complaint history.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    create_res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    complaint_id = uuid.UUID(create_res.json()["id"])

    # Simulate subsequent admin updates
    upd2 = ComplaintUpdate(
        complaint_id=complaint_id,
        updated_by_user_id=admin_user.id,
        old_status=ComplaintStatus.SUBMITTED,
        new_status=ComplaintStatus.UNDER_REVIEW,
        remark="Field inspector assigned.",
        progress_percentage=20,
    )
    upd3 = ComplaintUpdate(
        complaint_id=complaint_id,
        updated_by_user_id=admin_user.id,
        old_status=ComplaintStatus.UNDER_REVIEW,
        new_status=ComplaintStatus.IN_PROGRESS,
        remark="Repair crew dispatched.",
        progress_percentage=50,
    )
    db_session.add_all([upd2, upd3])
    db_session.commit()

    detail_res = auth_client.get(f"/api/v1/complaints/{complaint_id}", headers=headers)
    updates = detail_res.json()["updates"]
    assert len(updates) == 3
    assert updates[0]["new_status"] == "SUBMITTED"
    assert updates[1]["new_status"] == "UNDER_REVIEW"
    assert updates[2]["new_status"] == "IN_PROGRESS"


def test_20_image_metadata_does_not_expose_raw_exif(auth_client, citizen_user, sample_jpeg_with_exif_bytes):
    """Test 20: Raw EXIF parameters (camera serials, user info) are never exposed."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("photo.jpg", sample_jpeg_with_exif_bytes, "image/jpeg"))]
    data = {
        "title": "EXIF privacy test",
        "description": "Verifying that raw EXIF dictionary is not exposed.",
        "category": "ROADS",
        "latitude": 16.506167,
        "longitude": 80.648000,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 201
    images = res.json()["images"]
    assert len(images) == 1
    # Only safe coordinate floats are exposed
    assert "camera_model" not in images[0]
    assert "serial_number" not in images[0]
    assert "raw_exif" not in images[0]


def test_21_exif_gps_is_parsed_when_present(auth_client, citizen_user, sample_jpeg_with_exif_bytes):
    """Test 21: EXIF GPS coordinates are extracted into ComplaintImage."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("photo.jpg", sample_jpeg_with_exif_bytes, "image/jpeg"))]
    data = {
        "title": "EXIF GPS parsing test",
        "description": "Verifying that GPS EXIF coordinates are extracted.",
        "category": "ROADS",
        "latitude": 16.506167,
        "longitude": 80.648000,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 201
    img = res.json()["images"][0]
    assert img["latitude"] is not None
    assert img["longitude"] is not None
    assert img["latitude"] == pytest.approx(16.506167, abs=1e-4)
    assert img["longitude"] == pytest.approx(80.648000, abs=1e-4)


def test_22_mismatched_exif_gps_is_handled_gracefully(auth_client, citizen_user, sample_jpeg_with_exif_bytes):
    """Test 22: Mismatched EXIF GPS does not reject complaint creation."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("photo.jpg", sample_jpeg_with_exif_bytes, "image/jpeg"))]
    # Complaint declared in London, but photo EXIF is in Vijayawada
    data = {
        "title": "Mismatched EXIF location",
        "description": "Photo taken elsewhere but submitted with coordinates.",
        "category": "ROADS",
        "latitude": 51.5074,
        "longitude": -0.1278,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 201
    assert res.json()["latitude"] == pytest.approx(51.5074, abs=1e-4)


def test_23_missing_exif_gps_allows_normal_creation(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 23: Images without EXIF GPS still succeed using declared complaint coordinates."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("no_exif.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "No EXIF test",
        "description": "Image has no GPS tags; complaint should still be created.",
        "category": "ROADS",
        "latitude": 16.506174,
        "longitude": 80.648015,
        "location_source": "MANUAL",
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 201
    assert res.json()["location_source"] == "MANUAL"
    assert res.json()["images"][0]["latitude"] is None


def test_24_image_storage_failure_rolls_back_transaction(auth_client, citizen_user, sample_jpeg_bytes, db_session):
    """Test 24: If image storage fails, no orphaned complaint record is created."""
    class FailingStorageProvider(ImageStorageProvider):
        async def upload_image(self, file_bytes, filename, content_type):
            raise ConnectionError("Storage provider unreachable")
        async def delete_image(self, public_id):
            return True

    original_provider = get_image_storage_provider()
    set_image_storage_provider(FailingStorageProvider())

    try:
        headers = _get_auth_headers(citizen_user)
        files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
        data = {
            "title": "Rollback storage failure test",
            "description": "This complaint should not persist because storage fails.",
            "category": "ROADS",
            "latitude": 16.5,
            "longitude": 80.6,
        }
        res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
        assert res.status_code == 500

        # Verify no orphaned record in database
        orphaned = db_session.scalar(select(Complaint).where(Complaint.title == "Rollback storage failure test"))
        assert orphaned is None
    finally:
        set_image_storage_provider(original_provider)


def test_25_dashboard_stats_returns_real_data(auth_client, citizen_user, sample_jpeg_bytes, db_session):
    """Test 25: Dashboard queries return accurate aggregate metrics."""
    headers = _get_auth_headers(citizen_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]

    # Create one complaint
    data = {
        "title": "Dashboard stats test item",
        "description": "Checking citizen dashboard counter incrementation.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)

    res = auth_client.get("/api/v1/complaints/stats/citizen", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_submitted"] >= 1
    assert stats["in_progress"] == 0
    assert stats["resolved"] == 0
    assert stats["community_upvotes"] == 0
    assert len(stats["recent_complaints"]) >= 1


def test_26_complaint_submission_rate_limit(auth_client, citizen_user, sample_jpeg_bytes):
    """Test 26: Submitting more than 5 complaints rapidly triggers 429 Too Many Requests."""
    headers = _get_auth_headers(citizen_user)

    for i in range(5):
        files = [("images", (f"img_{i}.jpg", sample_jpeg_bytes, "image/jpeg"))]
        data = {
            "title": f"Rate limit complaint #{i+1}",
            "description": "Rapid succession test for complaint rate limiter.",
            "category": "ROADS",
            "latitude": 16.5,
            "longitude": 80.6,
        }
        res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
        assert res.status_code == 201

    # 6th submission within the window should be blocked with 429
    files = [("images", ("img_blocked.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Blocked 6th complaint submission",
        "description": "This request should be rejected by rate limiter.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res_blocked = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res_blocked.status_code == 429
    msg = res_blocked.json().get("message") or res_blocked.json().get("detail", "")
    assert "rate limit exceeded" in msg.lower()
    assert "retry-after" in res_blocked.headers


def test_27_admin_cannot_submit_citizen_complaint(auth_client, admin_user, sample_jpeg_bytes):
    """Test 27: Admin role is forbidden (403) from submitting citizen complaints."""
    headers = _get_auth_headers(admin_user)
    files = [("images", ("img.jpg", sample_jpeg_bytes, "image/jpeg"))]
    data = {
        "title": "Admin submitting citizen complaint",
        "description": "Admin attempting to report through citizen portal.",
        "category": "ROADS",
        "latitude": 16.5,
        "longitude": 80.6,
    }
    res = auth_client.post("/api/v1/complaints", data=data, files=files, headers=headers)
    assert res.status_code == 403
