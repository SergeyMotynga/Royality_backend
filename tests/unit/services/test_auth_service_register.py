from __future__ import annotations

import time
from dataclasses import dataclass

import pytest
from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    InvalidVerificationCodeError,
    RateLimitExceededError,
    VerificationCodeAttemptsExceededError,
    VerificationCodeExpiredError,
    VerificationCodeResendNotAllowedError,
)
from backend.app.models.user import User
from backend.app.services.auth import AuthCodeState, AuthService

pytestmark = pytest.mark.unit


class _FakeAuthRateLimiter:
    def __init__(self, *, should_raise: Exception | None = None) -> None:
        self.should_raise = should_raise
        self.calls: list[tuple[str, str | None]] = []

    async def check_auth_limits(self, *, phone_number: str, ip_address: str | None) -> None:
        self.calls.append((phone_number, ip_address))
        if self.should_raise is not None:
            raise self.should_raise


@dataclass(slots=True)
class _CreateUserCall:
    phone_number: str
    is_verified: bool


class _FakeUserRepo:
    def __init__(self, *, existing_user: User | None = None) -> None:
        self.existing_user = existing_user
        self.requested_phone_number: str | None = None
        self.create_calls: list[_CreateUserCall] = []
        self.mark_user_verified_calls: list[User] = []

    async def get_by_phone_number(self, phone_number: str) -> User | None:
        self.requested_phone_number = phone_number
        return self.existing_user

    async def create_user(self, *, phone_number: str, is_verified: bool = False) -> User:
        self.create_calls.append(
            _CreateUserCall(phone_number=phone_number, is_verified=is_verified)
        )
        return User(phone_number=phone_number, is_verified=is_verified)

    async def mark_user_verified(self, *, user: User) -> User:
        self.mark_user_verified_calls.append(user)
        user.is_verified = True
        return user


@dataclass(slots=True)
class _SavedCodeCall:
    phone_number: str
    code: str
    ttl_seconds: int
    max_attempts: int
    resend_cooldown_seconds: int


@dataclass(slots=True)
class _UpdateCodeCall:
    phone_number: str
    state: AuthCodeState


class _FakeVerificationCodeStore:
    def __init__(self, *, state_by_phone: dict[str, AuthCodeState] | None = None) -> None:
        self.state_by_phone = state_by_phone or {}
        self.save_calls: list[_SavedCodeCall] = []
        self.update_calls: list[_UpdateCodeCall] = []
        self.delete_calls: list[str] = []

    async def save_auth_code(
        self,
        *,
        phone_number: str,
        code: str,
        ttl_seconds: int,
        max_attempts: int,
        resend_cooldown_seconds: int,
    ) -> None:
        now = int(time.time())
        self.save_calls.append(
            _SavedCodeCall(
                phone_number=phone_number,
                code=code,
                ttl_seconds=ttl_seconds,
                max_attempts=max_attempts,
                resend_cooldown_seconds=resend_cooldown_seconds,
            )
        )
        self.state_by_phone[phone_number] = AuthCodeState(
            code=code,
            attempts_left=max_attempts,
            resend_available_at=now + resend_cooldown_seconds,
            expires_at=now + ttl_seconds,
        )

    async def get_auth_code(self, *, phone_number: str) -> AuthCodeState | None:
        return self.state_by_phone.get(phone_number)

    async def update_auth_code(self, *, phone_number: str, state: AuthCodeState) -> None:
        self.update_calls.append(_UpdateCodeCall(phone_number=phone_number, state=state))
        self.state_by_phone[phone_number] = state

    async def delete_auth_code(self, *, phone_number: str) -> None:
        self.delete_calls.append(phone_number)
        self.state_by_phone.pop(phone_number, None)


@dataclass(slots=True)
class _SmsTaskCall:
    phone_number: str
    code: str


class _FakeSmsTaskPublisher:
    def __init__(self) -> None:
        self.calls: list[_SmsTaskCall] = []

    def enqueue_phone_verification(self, *, phone_number: str, code: str) -> None:
        self.calls.append(_SmsTaskCall(phone_number=phone_number, code=code))


def _build_service(
    *,
    rate_limiter: _FakeAuthRateLimiter | None = None,
    user_repo: _FakeUserRepo | None = None,
    code_store: _FakeVerificationCodeStore | None = None,
    sms_publisher: _FakeSmsTaskPublisher | None = None,
) -> tuple[
    AuthService,
    _FakeAuthRateLimiter,
    _FakeUserRepo,
    _FakeVerificationCodeStore,
    _FakeSmsTaskPublisher,
]:
    limiter = rate_limiter or _FakeAuthRateLimiter()
    repo = user_repo or _FakeUserRepo()
    store = code_store or _FakeVerificationCodeStore()
    publisher = sms_publisher or _FakeSmsTaskPublisher()
    service = AuthService(
        rate_limiter=limiter,
        user_repo=repo,
        verification_code_store=store,
        sms_task_publisher=publisher,
        settings=Settings(
            AUTH_CODE_TTL_SECONDS=600,
            AUTH_CODE_MAX_ATTEMPTS=5,
            AUTH_CODE_RESEND_COOLDOWN_SECONDS=60,
        ),
    )
    return service, limiter, repo, store, publisher


@pytest.mark.asyncio
async def test_register_dispatches_code_and_checks_rate_limit() -> None:
    service, limiter, _, store, publisher = _build_service()

    result = await service.register(phone_number="8 (999) 123-45-67", ip_address="127.0.0.1")

    assert result.phone_number == "+79991234567"
    assert result.ttl_seconds == 600
    assert result.resend_cooldown_seconds == 60
    assert limiter.calls == [("+79991234567", "127.0.0.1")]
    assert len(store.save_calls) == 1
    save_call = store.save_calls[0]
    assert save_call.phone_number == "+79991234567"
    assert save_call.code.isdigit()
    assert len(save_call.code) == 6
    assert save_call.ttl_seconds == 600
    assert save_call.max_attempts == 5
    assert save_call.resend_cooldown_seconds == 60
    assert publisher.calls == [_SmsTaskCall(phone_number="+79991234567", code=save_call.code)]


@pytest.mark.asyncio
async def test_register_raises_if_rate_limit_exceeded() -> None:
    limiter = _FakeAuthRateLimiter(should_raise=RateLimitExceededError(retry_after_seconds=60))
    service, _, _, store, publisher = _build_service(rate_limiter=limiter)

    with pytest.raises(RateLimitExceededError):
        await service.register(phone_number="79991234567", ip_address="127.0.0.1")

    assert store.save_calls == []
    assert publisher.calls == []


@pytest.mark.asyncio
async def test_resend_verification_code_raises_if_cooldown_not_elapsed() -> None:
    now = int(time.time())
    current_state = AuthCodeState(
        code="123456",
        attempts_left=5,
        resend_available_at=now + 30,
        expires_at=now + 600,
    )
    store = _FakeVerificationCodeStore(state_by_phone={"+79991234567": current_state})
    service, limiter, _, _, publisher = _build_service(code_store=store)

    with pytest.raises(VerificationCodeResendNotAllowedError) as error_info:
        await service.resend_verification_code(phone_number="79991234567", ip_address="127.0.0.1")

    assert error_info.value.headers is not None
    assert "Retry-After" in error_info.value.headers
    assert limiter.calls == []
    assert len(store.save_calls) == 0
    assert publisher.calls == []


@pytest.mark.asyncio
async def test_resend_verification_code_dispatches_new_code_after_cooldown() -> None:
    now = int(time.time())
    current_state = AuthCodeState(
        code="123456",
        attempts_left=5,
        resend_available_at=now - 1,
        expires_at=now + 600,
    )
    store = _FakeVerificationCodeStore(state_by_phone={"+79991234567": current_state})
    service, limiter, _, _, publisher = _build_service(code_store=store)

    result = await service.resend_verification_code(
        phone_number="8 (999) 123-45-67",
        ip_address="127.0.0.1",
    )

    assert result.phone_number == "+79991234567"
    assert limiter.calls == [("+79991234567", "127.0.0.1")]
    assert len(store.save_calls) == 1
    assert len(publisher.calls) == 1


@pytest.mark.asyncio
async def test_verify_code_raises_when_state_missing() -> None:
    service, _, _, _, _ = _build_service()

    with pytest.raises(VerificationCodeExpiredError):
        await service.verify_code(phone_number="79991234567", code="123456")


@pytest.mark.asyncio
async def test_verify_code_raises_and_deletes_when_code_expired() -> None:
    now = int(time.time())
    expired_state = AuthCodeState(
        code="123456",
        attempts_left=5,
        resend_available_at=now - 10,
        expires_at=now - 1,
    )
    store = _FakeVerificationCodeStore(state_by_phone={"+79991234567": expired_state})
    service, _, _, _, _ = _build_service(code_store=store)

    with pytest.raises(VerificationCodeExpiredError):
        await service.verify_code(phone_number="79991234567", code="123456")

    assert store.delete_calls == ["+79991234567"]


@pytest.mark.asyncio
async def test_verify_code_decrements_attempts_for_invalid_code() -> None:
    now = int(time.time())
    state = AuthCodeState(
        code="123456",
        attempts_left=3,
        resend_available_at=now - 10,
        expires_at=now + 600,
    )
    store = _FakeVerificationCodeStore(state_by_phone={"+79991234567": state})
    service, _, _, _, _ = _build_service(code_store=store)

    with pytest.raises(InvalidVerificationCodeError):
        await service.verify_code(phone_number="79991234567", code="000000")

    assert len(store.update_calls) == 1
    assert store.update_calls[0].phone_number == "+79991234567"
    assert store.update_calls[0].state.attempts_left == 2
    assert store.delete_calls == []


@pytest.mark.asyncio
async def test_verify_code_raises_attempts_exceeded_and_deletes_state() -> None:
    now = int(time.time())
    state = AuthCodeState(
        code="123456",
        attempts_left=1,
        resend_available_at=now - 10,
        expires_at=now + 600,
    )
    store = _FakeVerificationCodeStore(state_by_phone={"+79991234567": state})
    service, _, _, _, _ = _build_service(code_store=store)

    with pytest.raises(VerificationCodeAttemptsExceededError):
        await service.verify_code(phone_number="79991234567", code="000000")

    assert store.update_calls == []
    assert store.delete_calls == ["+79991234567"]


@pytest.mark.asyncio
async def test_verify_code_creates_new_user_when_missing() -> None:
    now = int(time.time())
    state = AuthCodeState(
        code="123456",
        attempts_left=5,
        resend_available_at=now - 10,
        expires_at=now + 600,
    )
    store = _FakeVerificationCodeStore(state_by_phone={"+79991234567": state})
    service, _, repo, _, _ = _build_service(code_store=store)

    result = await service.verify_code(phone_number="79991234567", code="123456")

    assert result.is_new_user is True
    assert result.user.phone_number == "+79991234567"
    assert result.user.is_verified is True
    assert repo.create_calls == [_CreateUserCall(phone_number="+79991234567", is_verified=True)]


@pytest.mark.asyncio
async def test_verify_code_marks_existing_user_as_verified() -> None:
    now = int(time.time())
    state = AuthCodeState(
        code="123456",
        attempts_left=5,
        resend_available_at=now - 10,
        expires_at=now + 600,
    )
    existing_user = User(phone_number="+79991234567", is_verified=False)
    store = _FakeVerificationCodeStore(state_by_phone={"+79991234567": state})
    repo = _FakeUserRepo(existing_user=existing_user)
    service, _, _, _, _ = _build_service(user_repo=repo, code_store=store)

    result = await service.verify_code(phone_number="79991234567", code="123456")

    assert result.is_new_user is False
    assert result.user.is_verified is True
    assert repo.mark_user_verified_calls == [existing_user]
    assert repo.create_calls == []


@pytest.mark.asyncio
async def test_verify_code_returns_existing_verified_user_without_extra_updates() -> None:
    now = int(time.time())
    state = AuthCodeState(
        code="123456",
        attempts_left=5,
        resend_available_at=now - 10,
        expires_at=now + 600,
    )
    existing_user = User(phone_number="+79991234567", is_verified=True)
    store = _FakeVerificationCodeStore(state_by_phone={"+79991234567": state})
    repo = _FakeUserRepo(existing_user=existing_user)
    service, _, _, _, _ = _build_service(user_repo=repo, code_store=store)

    result = await service.verify_code(phone_number="79991234567", code="123456")

    assert result.is_new_user is False
    assert result.user is existing_user
    assert repo.mark_user_verified_calls == []
    assert repo.create_calls == []
