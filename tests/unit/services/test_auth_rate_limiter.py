from __future__ import annotations

import pytest
from backend.app.adapters.auth.rate_limiter import RedisRegisterRateLimiter
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
async def test_rate_limiter_increments_email_and_ip_counters() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisRegisterRateLimiter(
        redis_client=redis_client,
        max_requests_per_email=5,
        max_requests_per_ip=10,
        window_seconds=60,
    )

    await limiter.check_register_limits(email="user@example.com", ip_address="127.0.0.1")

    assert redis_client.counters["auth:register:email:user@example.com"] == 1
    assert redis_client.counters["auth:register:ip:127.0.0.1"] == 1
    assert redis_client.expire_calls == [
        ("auth:register:email:user@example.com", 60),
        ("auth:register:ip:127.0.0.1", 60),
    ]


@pytest.mark.asyncio
async def test_rate_limiter_raises_when_email_limit_exceeded() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisRegisterRateLimiter(
        redis_client=redis_client,
        max_requests_per_email=1,
        max_requests_per_ip=10,
        window_seconds=60,
    )

    await limiter.check_register_limits(email="user@example.com", ip_address="127.0.0.1")

    with pytest.raises(RateLimitExceededError):
        await limiter.check_register_limits(email="user@example.com", ip_address="127.0.0.1")


@pytest.mark.asyncio
async def test_rate_limiter_sets_expire_only_for_first_request_in_window() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisRegisterRateLimiter(
        redis_client=redis_client,
        max_requests_per_email=5,
        max_requests_per_ip=10,
        window_seconds=60,
    )

    await limiter.check_register_limits(email="user@example.com", ip_address="127.0.0.1")
    await limiter.check_register_limits(email="user@example.com", ip_address="127.0.0.1")

    assert redis_client.expire_calls == [
        ("auth:register:email:user@example.com", 60),
        ("auth:register:ip:127.0.0.1", 60),
    ]


@pytest.mark.asyncio
async def test_rate_limiter_skips_ip_limit_for_missing_ip() -> None:
    redis_client = _FakeRedisCounterClient()
    limiter = RedisRegisterRateLimiter(
        redis_client=redis_client,
        max_requests_per_email=5,
        max_requests_per_ip=10,
        window_seconds=60,
    )

    await limiter.check_register_limits(email="user@example.com", ip_address=None)

    assert redis_client.counters == {"auth:register:email:user@example.com": 1}
    assert redis_client.expire_calls == [("auth:register:email:user@example.com", 60)]
