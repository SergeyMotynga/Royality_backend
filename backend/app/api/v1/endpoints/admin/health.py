"""Админские endpoint-ы для проверки доступности сервиса."""

from fastapi import APIRouter

router = APIRouter(tags=["admin"])


@router.get("/health")
async def admin_healthcheck() -> dict[str, str]:
    """Проверяет, что админская часть API отвечает."""
    return {"status": "ok", "scope": "admin"}
