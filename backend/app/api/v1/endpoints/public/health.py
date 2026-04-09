"""Публичный health endpoint."""

from fastapi import APIRouter

from backend.app.services.health_service import build_health_payload

router = APIRouter(tags=["public"])


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    """Проверяет доступность публичного контура API."""
    return build_health_payload(scope="public")
