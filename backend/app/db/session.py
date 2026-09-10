import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("civicpulse.db")

# Create synchronous engine using standard driver (psycopg2 or psycopg)
# For SQLite or PostgreSQL, connection arguments vary:
connect_args = {}
if settings.sync_database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=connect_args,
)

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
