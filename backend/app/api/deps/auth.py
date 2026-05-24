"""DI-провайдеры auth-сценариев."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.adapters.auth import RedisVerificationCodeStore, build_auth_rate_limiter
from backend.app.core.config import Settings, get_settings
from backend.app.crud import UserCrud
from backend.app.db.session import get_db_session
from backend.app.services.auth import AuthService, SmsTaskPublisher


class NoopSmsTaskPublisher:
    """Временный publisher: не отправляет SMS, пока провайдер не подключен."""

    def enqueue_phone_verification(self, *, phone_number: str, code: str) -> None:
        """Сохраняет совместимость контракта до подключения реальной отправки."""
        _ = phone_number, code


@lru_cache
def _build_redis_client(redis_url: str) -> Redis:
    """Создает и кэширует Redis-клиент по URL из настроек."""
    return Redis.from_url(redis_url, decode_responses=True)


def get_redis_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Redis:
    """Возвращает Redis-клиент для адаптеров auth-сервиса."""
    return _build_redis_client(settings.redis_url)


def get_sms_task_publisher() -> SmsTaskPublisher:
    """Возвращает publisher задач отправки SMS."""
    return NoopSmsTaskPublisher()


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    sms_task_publisher: Annotated[SmsTaskPublisher, Depends(get_sms_task_publisher)],
) -> AuthService:
    """Собирает AuthService с инфраструктурными адаптерами."""
    user_repo = UserCrud(session=session)
    rate_limiter = build_auth_rate_limiter(redis_client=redis_client, settings=settings)
    verification_code_store = RedisVerificationCodeStore(redis_client=redis_client)
    return AuthService(
        rate_limiter=rate_limiter,
        user_repo=user_repo,
        verification_code_store=verification_code_store,
        sms_task_publisher=sms_task_publisher,
        settings=settings,
    )

