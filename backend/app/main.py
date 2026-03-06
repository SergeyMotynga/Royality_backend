"""Модуль запуска и настройки FastAPI-приложения."""

from fastapi import FastAPI

from backend.app.api.routers import api_router
from backend.app.core.config import get_settings
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.logging import setup_logging

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title=settings.app_title)
register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["health"])
async def root_healthcheck() -> dict[str, str]:
    """Проверяет, что сервис отвечает на запросы."""
    return {"status": "ok", "scope": "root"}
