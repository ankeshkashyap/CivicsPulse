import pytest
import shapely.wkt
import geoalchemy2.admin.dialects.sqlite as gas
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.email_service import get_email_provider, ConsoleEmailProvider
from app.services.auth_service import _ip_request_timestamps

from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geometry

# Compile Geometry as GEOMETRY in SQLite dialect to allow native column creation
@compiles(Geometry, "sqlite")
def compile_geom_sqlite(type_, compiler, **kw):
    return "GEOMETRY"

# Bypass SpatiaLite recovery and index management events in pure SQLite test environments
gas.before_create = lambda *a, **k: None
gas.after_create = lambda *a, **k: None
gas.before_drop = lambda *a, **k: None
gas.after_drop = lambda *a, **k: None



@event.listens_for(Engine, "connect")
def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configures SQLite connections with foreign key support and lightweight GIS function mocks."""
    if hasattr(dbapi_connection, "create_function"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        def _geom_from_ewkt(val):
            if not val:
                return None
            wkt_str = val.split(";")[-1] if isinstance(val, str) else str(val)
            return shapely.wkt.loads(wkt_str).wkb

        dbapi_connection.create_function("GeomFromEWKT", 1, _geom_from_ewkt)
        dbapi_connection.create_function("AsEWKT", 1, lambda val: val)
        dbapi_connection.create_function("AsEWKB", 1, lambda val: val)
        dbapi_connection.create_function("AsBinary", 1, lambda val: val)



from app.core.rate_limit import reset_complaint_rate_limits
from app.services.image_storage import get_image_storage_provider, MockImageStorageProvider, set_image_storage_provider

@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Clears in-memory rate limit caches and mock storage between test runs."""
    _ip_request_timestamps.clear()
    reset_complaint_rate_limits()
    storage = get_image_storage_provider()
    if isinstance(storage, MockImageStorageProvider):
        storage.clear()
    yield
    _ip_request_timestamps.clear()
    reset_complaint_rate_limits()


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Generates valid minimal JPEG image bytes."""
    import io
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (64, 64), color="green")
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def sample_jpeg_with_exif_bytes() -> bytes:
    """Generates valid JPEG image bytes containing GPS EXIF coordinates for Vijayawada (16.506167 N, 80.648000 E)."""
    import io
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (64, 64), color="blue")
    exif = img.getexif()
    gps_ifd = exif.get_ifd(0x8825)
    gps_ifd[1] = "N"
    gps_ifd[2] = (16.0, 30.0, 22.2)
    gps_ifd[3] = "E"
    gps_ifd[4] = (80.0, 38.0, 52.8)
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()




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
