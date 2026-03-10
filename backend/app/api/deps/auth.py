"""DI-провайдеры auth-сценариев."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.adapters.auth import (
    RedisVerificationCodeStore,
    SqlAlchemyUserRepo,
    build_register_rate_limiter,
)
from backend.app.core.config import Settings, get_settings
from backend.app.db.session import get_db_session
from backend.app.services.auth import AuthService, EmailTaskPublisher


class NoopEmailTaskPublisher:
    """Временный publisher: не отправляет письма, пока Celery-задачи не подключены."""

    def enqueue_email_verification(self, *, email: str, code: str) -> None:
        """Сохраняет совместимость контракта до подключения реального воркера."""
        _ = email, code


@lru_cache
def _build_redis_client(redis_url: str) -> Redis:
    """Создает и кэширует Redis-клиент по URL из настроек."""
    return Redis.from_url(redis_url, decode_responses=True)


def get_redis_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Redis:
    """Возвращает Redis-клиент для адаптеров auth-сервиса."""
    return _build_redis_client(settings.redis_url)


def get_email_task_publisher() -> EmailTaskPublisher:
    """Возвращает publisher задач отправки email."""
    return NoopEmailTaskPublisher()


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    email_task_publisher: Annotated[EmailTaskPublisher, Depends(get_email_task_publisher)],
) -> AuthService:
    """Собирает AuthService с инфраструктурными адаптерами."""
    user_repo = SqlAlchemyUserRepo(session=session)
    rate_limiter = build_register_rate_limiter(redis_client=redis_client, settings=settings)
    verification_code_store = RedisVerificationCodeStore(redis_client=redis_client)
    return AuthService(
        rate_limiter=rate_limiter,
        user_repo=user_repo,
        verification_code_store=verification_code_store,
        email_task_publisher=email_task_publisher,
        settings=settings,
    )
