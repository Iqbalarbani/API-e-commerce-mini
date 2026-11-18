"""Service layer for system health verification."""

from fastapi import status
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.core.exceptions import AppException
from app.repositories.health_repository import HealthRepository
from app.schemas.health import HealthResponse


class HealthService:
    """Coordinates health checks across application dependencies."""

    def __init__(self, repository: HealthRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    def get_health_status(self) -> HealthResponse:
        """Verify database connectivity and return overall service health."""
        try:
            self.repository.ping()
        except SQLAlchemyError as exc:
            raise AppException(
                code="DATABASE_UNAVAILABLE",
                message="Database connection failed.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        return HealthResponse(
            status="ok",
            database="connected",
            app_name=self.settings.APP_NAME,
            environment=self.settings.APP_ENV,
        )
