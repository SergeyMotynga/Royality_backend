from __future__ import annotations

import pytest
from backend.app.adapters.auth.rate_limiter import RedisAuthRateLimiter, build_auth_rate_limiter
from backend.app.core.config import Settings
from backend.app.core.exceptions import RateLimitExceededError

pytestmark = pytest.mark.unit


class _FakeRedisCounterClient:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.expire_calls: list[tuple[str, int]] = []

    async def incr(self, key: str) -> int:
        value = self.counters.get(key, 0) + 1
        self.counters[key] = value
        return value

    async def expire(self, key: str, ttl_seconds: int) -> None:
        self.expire_calls.append((key, ttl_seconds))


@pytest.mark.asyncio
async def test_rate_limiter_increments_phone_and_ip_counters() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisAuthRateLimiter(
        redis_client=redis_client,
        max_requests_per_phone=5,
        max_requests_per_ip=10,
        window_seconds=60,
    )

    await limiter.check_auth_limits(phone_number="+79991234567", ip_address="127.0.0.1")

    assert redis_client.counters["auth:phone:+79991234567"] == 1
    assert redis_client.counters["auth:ip:127.0.0.1"] == 1
    assert redis_client.expire_calls == [
        ("auth:phone:+79991234567", 60),
        ("auth:ip:127.0.0.1", 60),
    ]


@pytest.mark.asyncio
async def test_rate_limiter_raises_when_phone_limit_exceeded() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisAuthRateLimiter(
        redis_client=redis_client,
        max_requests_per_phone=1,
        max_requests_per_ip=10,
        window_seconds=60,
    )

    await limiter.check_auth_limits(phone_number="+79991234567", ip_address="127.0.0.1")

    with pytest.raises(RateLimitExceededError) as error_info:
        await limiter.check_auth_limits(phone_number="+79991234567", ip_address="127.0.0.1")

    assert error_info.value.headers == {"Retry-After": "60"}


@pytest.mark.asyncio
async def test_rate_limiter_sets_expire_only_for_first_request_in_window() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisAuthRateLimiter(
        redis_client=redis_client,
        max_requests_per_phone=5,
        max_requests_per_ip=10,
        window_seconds=60,
    )

    await limiter.check_auth_limits(phone_number="+79991234567", ip_address="127.0.0.1")
    await limiter.check_auth_limits(phone_number="+79991234567", ip_address="127.0.0.1")

    assert redis_client.expire_calls == [
        ("auth:phone:+79991234567", 60),
        ("auth:ip:127.0.0.1", 60),
    ]


@pytest.mark.asyncio
async def test_rate_limiter_raises_with_retry_after_when_ip_limit_exceeded() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisAuthRateLimiter(
        redis_client=redis_client,
        max_requests_per_phone=10,
        max_requests_per_ip=1,
        window_seconds=120,
    )

    await limiter.check_auth_limits(phone_number="+79991234567", ip_address="127.0.0.1")

    with pytest.raises(RateLimitExceededError) as error_info:
        await limiter.check_auth_limits(phone_number="+71111111111", ip_address="127.0.0.1")

    assert error_info.value.headers == {"Retry-After": "120"}


@pytest.mark.asyncio
async def test_rate_limiter_skips_ip_limit_for_missing_ip() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisAuthRateLimiter(
        redis_client=redis_client,
        max_requests_per_phone=5,
        max_requests_per_ip=10,
        window_seconds=60,
    )

    await limiter.check_auth_limits(phone_number="+79991234567", ip_address=None)

    assert redis_client.counters == {"auth:phone:+79991234567": 1}
    assert redis_client.expire_calls == [("auth:phone:+79991234567", 60)]


def test_build_rate_limiter_uses_settings_values() -> None:
    redis_client = _FakeRedisCounterClient()
    settings = Settings(
        AUTH_RATE_LIMIT_MAX_REQUESTS_PER_PHONE=9,
        AUTH_RATE_LIMIT_MAX_REQUESTS_PER_IP=42,
        AUTH_RATE_LIMIT_WINDOW_SECONDS=777,
    )

    limiter = build_auth_rate_limiter(redis_client=redis_client, settings=settings)

    assert limiter.max_requests_per_phone == 9
    assert limiter.max_requests_per_ip == 42
    assert limiter.window_seconds == 777
