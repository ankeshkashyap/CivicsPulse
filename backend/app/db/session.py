import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("civicpulse.db")

# Create synchronous engine using standard driver (psycopg2 or psycopg)
# For SQLite or PostgreSQL, connection arguments vary:
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if settings.sync_database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    import shapely.wkt
    import geoalchemy2.admin.dialects.sqlite as gas
    from sqlalchemy import event
    from sqlalchemy.ext.compiler import compiles
    from geoalchemy2 import Geometry

    @compiles(Geometry, "sqlite")
    def compile_geom_sqlite(type_, compiler, **kw):
        return "GEOMETRY"

    gas.before_create = lambda *a, **k: None
    gas.after_create = lambda *a, **k: None
    gas.before_drop = lambda *a, **k: None
    gas.after_drop = lambda *a, **k: None
else:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_engine(
    settings.sync_database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

if settings.sync_database_url.startswith("sqlite"):
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def configure_sqlite_connection(dbapi_connection, connection_record):
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

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> dict:
    """Utility function to test database connectivity cleanly."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"connected": True, "message": "Database connection healthy"}
    except Exception as exc:
        logger.warning(f"Database connection check failed: {exc}")
        return {"connected": False, "message": str(exc)}
