from __future__ import annotations

import pytest
from backend.app.api.deps.auth import (
    NoopEmailTaskPublisher,
    _build_redis_client,
    get_auth_service,
    get_email_task_publisher,
    get_redis_client,
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


def test_noop_email_task_publisher_implements_contract() -> None:
    publisher = NoopEmailTaskPublisher()
    result = publisher.enqueue_email_verification(email="user@example.com", code="123456")
    assert result is None


def test_get_email_task_publisher_returns_noop_implementation() -> None:
    publisher = get_email_task_publisher()
    assert isinstance(publisher, NoopEmailTaskPublisher)


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
        REGISTER_RATE_LIMIT_MAX_REQUESTS_PER_EMAIL=7,
        REGISTER_RATE_LIMIT_MAX_REQUESTS_PER_IP=21,
        REGISTER_RATE_LIMIT_WINDOW_SECONDS=120,
    )
    fake_session = object()
    fake_redis = _FakeRedisClient()
    publisher = NoopEmailTaskPublisher()

    service = await get_auth_service(
        session=fake_session,  # type: ignore[arg-type]
        settings=settings,
        redis_client=fake_redis,  # type: ignore[arg-type]
        email_task_publisher=publisher,
    )

    assert isinstance(service, AuthService)
    assert service.settings.register_rate_limit_window_seconds == 120
