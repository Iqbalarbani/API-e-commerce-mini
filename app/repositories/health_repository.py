"""Repository for database health check queries."""

from sqlalchemy.orm import Session

from app.core.database import check_db_connection


class HealthRepository:
    """Encapsulates low-level database connectivity checks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def ping(self) -> bool:
        """Execute a lightweight query to verify database availability."""
        return check_db_connection(self.db)
