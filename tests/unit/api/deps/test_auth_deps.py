from __future__ import annotations

import pytest
from backend.app.api.deps.auth import (
    NoopSmsTaskPublisher,
    _build_redis_client,
    get_auth_service,
    get_redis_client,
    get_sms_task_publisher,
)
from backend.app.core.config import Settings
from backend.app.services.auth import AuthService

pytestmark = pytest.mark.unit


class _FakeRedisClient:
    async def incr(self, _key: str) -> int:
        return 1

    async def expire(self, _key: str, _ttl_seconds: int) -> None:
        return None

    async def set(self, _key: str, _value: str, *, ex: int) -> bool:
        _ = ex
        return True

    async def get(self, _key: str) -> str | None:
        return None

    async def delete(self, _key: str) -> int:
        return 1


def test_noop_sms_task_publisher_implements_contract() -> None:
    publisher = NoopSmsTaskPublisher()
    result = publisher.enqueue_phone_verification(phone_number="79991234567", code="123456")
    assert result is None


def test_get_sms_task_publisher_returns_noop_implementation() -> None:
    publisher = get_sms_task_publisher()
    assert isinstance(publisher, NoopSmsTaskPublisher)


def test_get_redis_client_uses_cached_builder() -> None:
    _build_redis_client.cache_clear()
    settings = Settings(REDIS_URL="redis://localhost:6379/0")

    client_first = get_redis_client(settings=settings)
    client_second = get_redis_client(settings=settings)

    assert client_first is client_second


@pytest.mark.asyncio
async def test_get_auth_service_builds_service_with_adapters() -> None:
    settings = Settings(
        REDIS_URL="redis://localhost:6379/0",
        AUTH_RATE_LIMIT_MAX_REQUESTS_PER_PHONE=7,
        AUTH_RATE_LIMIT_MAX_REQUESTS_PER_IP=21,
        AUTH_RATE_LIMIT_WINDOW_SECONDS=120,
        AUTH_CODE_TTL_SECONDS=600,
    )
    fake_session = object()
    fake_redis = _FakeRedisClient()
    publisher = NoopSmsTaskPublisher()

    service = await get_auth_service(
        session=fake_session,  # type: ignore[arg-type]
        settings=settings,
        redis_client=fake_redis,  # type: ignore[arg-type]
        sms_task_publisher=publisher,
    )

    assert isinstance(service, AuthService)
    assert service.settings.auth_rate_limit_window_seconds == 120
    assert service.settings.auth_code_ttl_seconds == 600
