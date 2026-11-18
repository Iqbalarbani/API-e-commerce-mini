"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, Request, status

from app.core.config import get_settings
from app.core.dependencies import AdminUser, CurrentUser, DbSession
from app.core.rate_limit import limiter
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(db: DbSession) -> AuthService:
    """Construct AuthService with its repository."""
    return AuthService(repository=UserRepository(db))


def _login_limit() -> str:
    return get_settings().LOGIN_RATE_LIMIT


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register akun customer baru",
)
def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return UserResponse.model_validate(service.register(payload))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login dan dapatkan JWT",
)
@limiter.limit(_login_limit)
def login(
    request: Request,
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return service.login(payload)


@router.get("/me", response_model=UserResponse, summary="Profil user saat ini")
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/admin-check", summary="Endpoint khusus admin")
def admin_check(admin: AdminUser) -> dict[str, str]:
    return {"message": f"Halo admin {admin.full_name}"}
