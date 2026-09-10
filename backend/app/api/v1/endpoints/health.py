from fastapi import APIRouter, status
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import HealthResponse, DatabaseHealth

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="API and Database Health Status",
    description="Returns health status of the CivicPulse API server and PostgreSQL connectivity.",
)
def get_health() -> HealthResponse:
    """Thin route handler returning system operational health without embedded DB logic."""
    db_result = check_db_connection()

    db_health = DatabaseHealth(
        status="healthy" if db_result["connected"] else "unhealthy",
        connected=db_result["connected"],
        message=db_result["message"],
    )

    return HealthResponse(
        status="ok",
        project_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        version="0.1.0",
        database=db_health,
    )
