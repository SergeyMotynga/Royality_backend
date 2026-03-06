"""Публичные endpoint-ы для проверки доступности сервиса."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    """Проверяет, что публичная часть API отвечает."""
    return {"status": "ok", "scope": "public"}
