import uuid
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.city import City
from app.models.department import Department
from app.models.user import User
from app.models.complaint import Complaint
from app.models.complaint_image import ComplaintImage
from app.models.complaint_update import ComplaintUpdate
from app.models.upvote import Upvote
from app.models.enums import UserRole, ComplaintCategory, ComplaintSeverity, ComplaintStatus


@pytest.fixture
def db_session():
    """Provides an isolated in-memory transactional database session with foreign key enforcement."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_user_email_normalization_and_role_enum(db_session):
    """Verifies User creation, email normalization, and role enum support."""
    user = User(
        email="Citizen.Test@Example.Com ",
        full_name="Jane Doe",
        role=UserRole.CITIZEN,
    )
    db_session.add(user)
    db_session.commit()

    assert user.email == "citizen.test@example.com"
    assert user.role == UserRole.CITIZEN
    assert user.is_active is True
    assert user.is_verified is False
    assert user.id is not None
    assert user.created_at is not None


def test_user_email_uniqueness(db_session):
    """Verifies that duplicate emails cannot be stored."""
    user1 = User(email="duplicate@example.com", role=UserRole.CITIZEN)
    user2 = User(email="DUPLICATE@example.com", role=UserRole.ADMIN)

    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_city_and_department_models(db_session):
    """Verifies City and Department creation and unique constraints."""
    city = City(name="Vijayawada", state="Andhra Pradesh", country="India")
    db_session.add(city)
    db_session.commit()

    dept1 = Department(city_id=city.id, name="Public Health & Sanitation")
    db_session.add(dept1)
    db_session.commit()

    assert dept1.city_id == city.id
    assert len(city.departments) == 1
    assert city.departments[0].name == "Public Health & Sanitation"

    # Verify duplicate department in same city fails unique constraint
    dept2 = Department(city_id=city.id, name="Public Health & Sanitation")
    db_session.add(dept2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_complaint_enums_and_lifecycle(db_session):
    """Verifies Complaint category, severity, status enums, and location coordinates."""
    city = City(name="Vijayawada", state="Andhra Pradesh")
    user = User(email="reporter@example.com")
    db_session.add_all([city, user])
    db_session.commit()

    complaint = Complaint(
        city_id=city.id,
        user_id=user.id,
        title="Pothole on Main Ring Road",
        description="Hazardous pothole causing traffic slowdowns near Benz Circle.",
        category=ComplaintCategory.ROADS,
        severity=ComplaintSeverity.HIGH,
        status=ComplaintStatus.SUBMITTED,
        latitude=Decimal("16.506174"),
        longitude=Decimal("80.648015"),
    )
    db_session.add(complaint)
    db_session.commit()

    assert complaint.category == ComplaintCategory.ROADS
    assert complaint.severity == ComplaintSeverity.HIGH
    assert complaint.status == ComplaintStatus.SUBMITTED
    assert complaint.latitude == Decimal("16.506174")
    assert complaint.longitude == Decimal("80.648015")
    assert complaint.department_id is None


def test_complaint_image_and_update_models(db_session):
    """Verifies evidence image metadata and immutable audit updates."""
    city = City(name="Vijayawada", state="Andhra Pradesh")
    user = User(email="admin@civicpulse.org", role=UserRole.ADMIN)
    db_session.add_all([city, user])
    db_session.commit()

    complaint = Complaint(
        city_id=city.id,
        user_id=user.id,
        title="Streetlight Malfunction",
        description="Light fixture unlit for 3 days.",
        category=ComplaintCategory.STREETLIGHTS,
        severity=ComplaintSeverity.MEDIUM,
        latitude=Decimal("16.510000"),
        longitude=Decimal("80.640000"),
    )
    db_session.add(complaint)
    db_session.commit()

    image = ComplaintImage(
        complaint_id=complaint.id,
        image_url="https://res.cloudinary.com/civicpulse/image/upload/sample.jpg",
        public_id="civicpulse/complaints/sample_01",
        latitude=Decimal("16.510002"),
        longitude=Decimal("80.640005"),
    )
    update = ComplaintUpdate(
        complaint_id=complaint.id,
        updated_by_user_id=user.id,
        old_status=ComplaintStatus.SUBMITTED,
        new_status=ComplaintStatus.UNDER_REVIEW,
        remark="Issue verified by ward officer. Scheduling technician inspection.",
        progress_percentage=25,
    )
    db_session.add_all([image, update])
    db_session.commit()

    assert len(complaint.images) == 1
    assert complaint.images[0].public_id == "civicpulse/complaints/sample_01"
    assert len(complaint.updates) == 1
    assert complaint.updates[0].progress_percentage == 25
    assert complaint.updates[0].new_status == ComplaintStatus.UNDER_REVIEW
    assert complaint.updates[0].updated_by_user_id == user.id


def test_complaint_update_requires_actor(db_session):
    """Verifies that ComplaintUpdate strictly requires an accountable actor (updated_by_user_id)."""
    city = City(name="Vijayawada", state="Andhra Pradesh")
    user = User(email="actor.test@civicpulse.org")
    db_session.add_all([city, user])
    db_session.commit()

    complaint = Complaint(
        city_id=city.id,
        user_id=user.id,
        title="Overflowing Drain",
        description="Drain backing up into roadway.",
        category=ComplaintCategory.DRAINAGE,
        severity=ComplaintSeverity.HIGH,
        latitude=Decimal("16.515000"),
        longitude=Decimal("80.642000"),
    )
    db_session.add(complaint)
    db_session.commit()

    # Attempting to save an audit record without an accountable actor must fail
    update_without_actor = ComplaintUpdate(
        complaint_id=complaint.id,
        updated_by_user_id=None,
        new_status=ComplaintStatus.ASSIGNED,
    )
    db_session.add(update_without_actor)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_deletion_restricted_when_complaints_exist(db_session):
    """
    Verifies that physical deletion of a user is RESTRICTED when complaints reference them.
    Civic complaints must be preserved as civic history, and users deactivated via is_active=False.
    """
    city = City(name="Vijayawada", state="Andhra Pradesh")
    citizen = User(email="citizen.history@example.com")
    db_session.add_all([city, citizen])
    db_session.commit()

    complaint = Complaint(
        city_id=city.id,
        user_id=citizen.id,
        title="Broken Water Pipe",
        description="Potable water leak on sidewalk.",
        category=ComplaintCategory.WATER,
        severity=ComplaintSeverity.MEDIUM,
        latitude=Decimal("16.512000"),
        longitude=Decimal("80.644000"),
    )
    db_session.add(complaint)
    db_session.commit()

    complaint_id = complaint.id

    # 1. Attempting physical deletion of user must raise IntegrityError (RESTRICT constraint)
    db_session.delete(citizen)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Verify complaint still exists intact
    persisted_complaint = db_session.query(Complaint).filter_by(id=complaint_id).first()
    assert persisted_complaint is not None
    assert persisted_complaint.user_id == citizen.id

    # 2. Proper lifecycle deactivation (is_active=False) succeeds seamlessly
    citizen_record = db_session.query(User).filter_by(id=citizen.id).first()
    citizen_record.is_active = False
    db_session.commit()

    assert citizen_record.is_active is False
    assert db_session.query(Complaint).filter_by(id=complaint_id).first() is not None


def test_upvote_uniqueness_constraint(db_session):
    """Verifies that the same user cannot upvote the same complaint more than once."""
    city = City(name="Vijayawada", state="Andhra Pradesh")
    user = User(email="voter@example.com")
    db_session.add_all([city, user])
    db_session.commit()

    complaint = Complaint(
        city_id=city.id,
        user_id=user.id,
        title="Garbage accumulation",
        description="Commercial waste pile on sidewalk.",
        category=ComplaintCategory.GARBAGE,
        severity=ComplaintSeverity.LOW,
        latitude=Decimal("16.505000"),
        longitude=Decimal("80.645000"),
    )
    db_session.add(complaint)
    db_session.commit()

    # First upvote succeeds
    upvote1 = Upvote(complaint_id=complaint.id, user_id=user.id)
    db_session.add(upvote1)
    db_session.commit()

    assert len(complaint.upvotes) == 1

    # Second upvote from same user for same complaint must fail
    upvote2 = Upvote(complaint_id=complaint.id, user_id=user.id)
    db_session.add(upvote2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_complaint_deletion_cascades_to_images_and_upvotes(db_session):
    """Verifies that deleting a complaint cleanly cascades to images and upvotes."""
    city = City(name="Vijayawada", state="Andhra Pradesh")
    user = User(email="test.cascade@example.com")
    db_session.add_all([city, user])
    db_session.commit()

    complaint = Complaint(
        city_id=city.id,
        user_id=user.id,
        title="Drainage Blockage",
        description="Storm drain blocked with silt.",
        category=ComplaintCategory.DRAINAGE,
        severity=ComplaintSeverity.HIGH,
        latitude=Decimal("16.520000"),
        longitude=Decimal("80.650000"),
    )
    db_session.add(complaint)
    db_session.commit()

    image = ComplaintImage(
        complaint_id=complaint.id,
        image_url="https://example.com/drain.jpg",
        public_id="drain_01",
    )
    upvote = Upvote(complaint_id=complaint.id, user_id=user.id)
    db_session.add_all([image, upvote])
    db_session.commit()

    complaint_id = complaint.id
    db_session.delete(complaint)
    db_session.commit()

    # Images and upvotes should be removed by cascade
    assert db_session.query(ComplaintImage).filter_by(complaint_id=complaint_id).first() is None
    assert db_session.query(Upvote).filter_by(complaint_id=complaint_id).first() is None