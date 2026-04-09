"""Административный health endpoint."""

from fastapi import APIRouter, Depends

from backend.app.api.dependencies.auth import CurrentUser, get_current_superuser
from backend.app.services.health_service import build_health_payload

router = APIRouter(tags=["admin"])


@router.get("/health")
async def admin_healthcheck(
    current_user: CurrentUser = Depends(get_current_superuser),
) -> dict[str, str]:
    """Проверяет доступность административного контура API."""
    return build_health_payload(scope="admin", user_id=current_user.user_id)
