"""Health check API endpoint."""

from fastapi import APIRouter, Depends, status

from app.core.config import Settings, get_settings
from app.core.dependencies import DbSession
from app.repositories.health_repository import HealthRepository
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


def get_health_service(
    db: DbSession,
    settings: Settings = Depends(get_settings),
) -> HealthService:
    """Construct HealthService with injected repository and settings."""
    repository = HealthRepository(db=db)
    return HealthService(repository=repository, settings=settings)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Verify API availability and database connectivity.",
)
def health_check(
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """Return service and database health status."""
    return service.get_health_status()
