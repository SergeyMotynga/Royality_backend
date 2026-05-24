from __future__ import annotations

import json

import pytest
from backend.app.adapters.auth.constants import build_auth_code_key
from backend.app.adapters.auth.verification_code_store import RedisVerificationCodeStore
from backend.app.services.auth import AuthCodeState

pytestmark = pytest.mark.unit


class _FakeRedisValueClient:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}
        self.set_calls: list[tuple[str, str, int]] = []
        self.get_calls: list[str] = []
        self.delete_calls: list[str] = []

    async def set(self, key: str, value: str, *, ex: int) -> bool:
        self.storage[key] = value
        self.set_calls.append((key, value, ex))
        return True

    async def get(self, key: str) -> str | None:
        self.get_calls.append(key)
        return self.storage.get(key)

    async def delete(self, key: str) -> int:
        self.delete_calls.append(key)
        return 1 if self.storage.pop(key, None) is not None else 0


@pytest.mark.asyncio
async def test_store_saves_auth_code_payload_with_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.app.adapters.auth.verification_code_store.time.time",
        lambda: 1_700_000_000,
    )
    redis_client = _FakeRedisValueClient()
    store = RedisVerificationCodeStore(redis_client=redis_client)

    await store.save_auth_code(
        phone_number="+79991234567",
        code="123456",
        ttl_seconds=600,
        max_attempts=5,
        resend_cooldown_seconds=60,
    )

    assert len(redis_client.set_calls) == 1
    key, value, ttl = redis_client.set_calls[0]
    assert key == build_auth_code_key("+79991234567")
    assert ttl == 600

    payload = json.loads(value)
    assert payload["code"] == "123456"
    assert payload["attempts_left"] == 5
    assert payload["resend_available_at"] == 1_700_000_060
    assert payload["expires_at"] == 1_700_000_600


@pytest.mark.asyncio
async def test_store_returns_none_when_auth_code_missing() -> None:
    redis_client = _FakeRedisValueClient()
    store = RedisVerificationCodeStore(redis_client=redis_client)

    result = await store.get_auth_code(phone_number="+79991234567")

    assert result is None
    assert redis_client.get_calls == [build_auth_code_key("+79991234567")]


@pytest.mark.asyncio
async def test_store_parses_saved_state_when_auth_code_exists() -> None:
    redis_client = _FakeRedisValueClient()
    redis_client.storage[build_auth_code_key("+79991234567")] = json.dumps(
        {
            "code": "654321",
            "attempts_left": 3,
            "resend_available_at": 1_700_000_030,
            "expires_at": 1_700_000_600,
        }
    )
    store = RedisVerificationCodeStore(redis_client=redis_client)

    state = await store.get_auth_code(phone_number="+79991234567")

    assert state == AuthCodeState(
        code="654321",
        attempts_left=3,
        resend_available_at=1_700_000_030,
        expires_at=1_700_000_600,
    )


@pytest.mark.asyncio
async def test_store_updates_auth_code_with_remaining_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.app.adapters.auth.verification_code_store.time.time",
        lambda: 1_700_000_000,
    )
    redis_client = _FakeRedisValueClient()
    store = RedisVerificationCodeStore(redis_client=redis_client)
    state = AuthCodeState(
        code="222222",
        attempts_left=2,
        resend_available_at=1_700_000_020,
        expires_at=1_700_000_120,
    )

    await store.update_auth_code(phone_number="+79991234567", state=state)

    assert len(redis_client.set_calls) == 1
    key, value, ttl = redis_client.set_calls[0]
    assert key == build_auth_code_key("+79991234567")
    assert ttl == 120
    assert json.loads(value) == {
        "code": "222222",
        "attempts_left": 2,
        "resend_available_at": 1_700_000_020,
        "expires_at": 1_700_000_120,
    }


@pytest.mark.asyncio
async def test_store_deletes_auth_code_by_phone_number() -> None:
    redis_client = _FakeRedisValueClient()
    key = build_auth_code_key("+79991234567")
    redis_client.storage[key] = "payload"
    store = RedisVerificationCodeStore(redis_client=redis_client)

    await store.delete_auth_code(phone_number="+79991234567")

    assert redis_client.delete_calls == [key]
    assert key not in redis_client.storage
