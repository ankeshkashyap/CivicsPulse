import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.email_service import get_email_provider, ConsoleEmailProvider
from app.services.auth_service import _ip_request_timestamps


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Clears in-memory rate limit caches between test runs."""
    _ip_request_timestamps.clear()
    yield
    _ip_request_timestamps.clear()


@pytest.fixture(scope="module")
def client():
    """Provides a basic HTTP test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_engine():
    """Shared single in-memory SQLite engine with StaticPool across all threads."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Provides an isolated in-memory transactional database session with foreign key enforcement."""
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_client(test_engine):
    """Provides a TestClient with database session overridden by test database."""
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def email_provider():
    """Provides the active email provider and clears sent messages before each test."""
    provider = get_email_provider()
    if isinstance(provider, ConsoleEmailProvider):
        provider.clear()
    yield provider
    if isinstance(provider, ConsoleEmailProvider):
        provider.clear()
