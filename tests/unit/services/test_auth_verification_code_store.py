from __future__ import annotations

import json

import pytest
from backend.app.adapters.auth.verification_code_store import RedisVerificationCodeStore

pytestmark = pytest.mark.unit


class _FakeRedisValueClient:
    def __init__(self) -> None:
        self.set_calls: list[tuple[str, str, int]] = []

    async def set(self, key: str, value: str, *, ex: int) -> bool:
        self.set_calls.append((key, value, ex))
        return True


@pytest.mark.asyncio
async def test_store_saves_verification_code_payload_with_ttl() -> None:
    redis_client = _FakeRedisValueClient()
    store = RedisVerificationCodeStore(redis_client=redis_client)

    await store.save_email_verification_code(
        email="user@example.com",
        code="123456",
        ttl_seconds=600,
        max_attempts=5,
        resend_cooldown_seconds=60,
    )

    assert len(redis_client.set_calls) == 1
    key, value, ttl = redis_client.set_calls[0]
    assert key == "auth:verify:user@example.com"
    assert ttl == 600

    payload = json.loads(value)
    assert payload["code"] == "123456"
    assert payload["attempts_left"] == 5
    assert payload["resend_cooldown_seconds"] == 60
