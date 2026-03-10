from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import pytest
from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    EmailAlreadyRegisteredError,
    RateLimitExceededError,
    WeakPasswordError,
)
from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.services.auth import AuthService

pytestmark = pytest.mark.unit


class _FakeRegisterRateLimiter:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls: list[tuple[str, str | None]] = []

    async def check_register_limits(self, *, email: str, ip_address: str | None) -> None:
        self.calls.append((email, ip_address))
        if self.should_fail:
            raise RateLimitExceededError()


class _FakeUserRepo:
    def __init__(self, *, existing_user: User | None = None) -> None:
        self.existing_user = existing_user
        self.requested_email: str | None = None
        self.created_email: str | None = None
        self.created_password_hash: str | None = None

    async def get_by_email(self, email: str) -> User | None:
        self.requested_email = email
        return self.existing_user

    async def create_user(self, *, email: str, password_hash: str) -> User:
        self.created_email = email
        self.created_password_hash = password_hash
        return User(email=email, password_hash=password_hash)


@dataclass(slots=True)
class _SavedCodeCall:
    email: str
    code: str
    ttl_seconds: int
    max_attempts: int
    resend_cooldown_seconds: int


class _FakeVerificationCodeStore:
    def __init__(self) -> None:
        self.calls: list[_SavedCodeCall] = []

    async def save_email_verification_code(
        self,
        *,
        email: str,
        code: str,
        ttl_seconds: int,
        max_attempts: int,
        resend_cooldown_seconds: int,
    ) -> None:
        self.calls.append(
            _SavedCodeCall(
                email=email,
                code=code,
                ttl_seconds=ttl_seconds,
                max_attempts=max_attempts,
                resend_cooldown_seconds=resend_cooldown_seconds,
            )
        )


@dataclass(slots=True)
class _EmailTaskCall:
    email: str
    code: str


class _FakeEmailTaskPublisher:
    def __init__(self) -> None:
        self.calls: list[_EmailTaskCall] = []

    def enqueue_email_verification(self, *, email: str, code: str) -> None:
        self.calls.append(_EmailTaskCall(email=email, code=code))


def _existing_user() -> User:
    user = User(
        email="exists@example.com",
        password_hash=hash_password("existing-user-secret-value"),
    )
    user.id = UUID("00000000-0000-0000-0000-000000000001")
    return user


@pytest.mark.asyncio
async def test_register_creates_user_saves_code_and_enqueues_email() -> None:
    raw_value = "sample_value_123"
    rate_limiter = _FakeRegisterRateLimiter()
    user_repo = _FakeUserRepo()
    code_store = _FakeVerificationCodeStore()
    email_publisher = _FakeEmailTaskPublisher()
    service = AuthService(
        rate_limiter=rate_limiter,
        user_repo=user_repo,
        verification_code_store=code_store,
        email_task_publisher=email_publisher,
    )

    created_user = await service.register(
        email="  NewUser@Example.COM ",
        password=raw_value,
        ip_address="127.0.0.1",
    )

    assert created_user.email == "newuser@example.com"
    assert user_repo.requested_email == "newuser@example.com"
    assert user_repo.created_email == "newuser@example.com"
    assert user_repo.created_password_hash is not None
    assert user_repo.created_password_hash != raw_value

    assert rate_limiter.calls == [("newuser@example.com", "127.0.0.1")]

    assert len(code_store.calls) == 1
    saved_code = code_store.calls[0]
    assert saved_code.email == "newuser@example.com"
    assert saved_code.code.isdigit()
    assert len(saved_code.code) == 6
    assert saved_code.ttl_seconds == 600
    assert saved_code.max_attempts == 5
    assert saved_code.resend_cooldown_seconds == 60

    assert email_publisher.calls == [
        _EmailTaskCall(email="newuser@example.com", code=saved_code.code)
    ]


@pytest.mark.asyncio
async def test_register_raises_if_email_already_exists() -> None:
    raw_value = "sample_value_123"
    rate_limiter = _FakeRegisterRateLimiter()
    user_repo = _FakeUserRepo(existing_user=_existing_user())
    code_store = _FakeVerificationCodeStore()
    email_publisher = _FakeEmailTaskPublisher()
    service = AuthService(
        rate_limiter=rate_limiter,
        user_repo=user_repo,
        verification_code_store=code_store,
        email_task_publisher=email_publisher,
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(
            email="exists@example.com",
            password=raw_value,
            ip_address="127.0.0.1",
        )

    assert user_repo.created_email is None
    assert code_store.calls == []
    assert email_publisher.calls == []


@pytest.mark.asyncio
async def test_register_raises_if_rate_limit_exceeded() -> None:
    raw_value = "sample_value_123"
    rate_limiter = _FakeRegisterRateLimiter(should_fail=True)
    user_repo = _FakeUserRepo()
    code_store = _FakeVerificationCodeStore()
    email_publisher = _FakeEmailTaskPublisher()
    service = AuthService(
        rate_limiter=rate_limiter,
        user_repo=user_repo,
        verification_code_store=code_store,
        email_task_publisher=email_publisher,
    )

    with pytest.raises(RateLimitExceededError):
        await service.register(
            email="newuser@example.com",
            password=raw_value,
            ip_address="127.0.0.1",
        )

    assert user_repo.requested_email is None
    assert user_repo.created_email is None
    assert code_store.calls == []
    assert email_publisher.calls == []


@pytest.mark.asyncio
async def test_register_raises_if_password_is_weak() -> None:
    rate_limiter = _FakeRegisterRateLimiter()
    user_repo = _FakeUserRepo()
    code_store = _FakeVerificationCodeStore()
    email_publisher = _FakeEmailTaskPublisher()
    service = AuthService(
        rate_limiter=rate_limiter,
        user_repo=user_repo,
        verification_code_store=code_store,
        email_task_publisher=email_publisher,
    )

    with pytest.raises(WeakPasswordError):
        await service.register(
            email="newuser@example.com",
            password="weakpassword",  # noqa: S106
            ip_address="127.0.0.1",
        )

    assert rate_limiter.calls == []
    assert user_repo.requested_email is None
    assert user_repo.created_email is None
    assert code_store.calls == []
    assert email_publisher.calls == []


@pytest.mark.asyncio
async def test_register_uses_password_limits_from_settings() -> None:
    rate_limiter = _FakeRegisterRateLimiter()
    user_repo = _FakeUserRepo()
    code_store = _FakeVerificationCodeStore()
    email_publisher = _FakeEmailTaskPublisher()
    custom_settings = Settings(PASSWORD_MIN_LENGTH=10, PASSWORD_MAX_LENGTH=12)
    service = AuthService(
        rate_limiter=rate_limiter,
        user_repo=user_repo,
        verification_code_store=code_store,
        email_task_publisher=email_publisher,
        settings=custom_settings,
    )

    with pytest.raises(WeakPasswordError) as error_info:
        await service.register(
            email="newuser@example.com",
            password="a1!aaaaa",  # noqa: S106
            ip_address="127.0.0.1",
        )

    assert "короче 10" in error_info.value.message.lower()
    assert rate_limiter.calls == []
    assert user_repo.requested_email is None
    assert user_repo.created_email is None
    assert code_store.calls == []
    assert email_publisher.calls == []
