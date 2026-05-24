from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import pytest
from backend.app.api.v1.endpoints.public.auth import get_auth_service, get_client_ip
from backend.app.core.exceptions import (
    InvalidVerificationCodeError,
    RateLimitExceededError,
    VerificationCodeResendNotAllowedError,
)
from backend.app.main import app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@dataclass(slots=True)
class _FakeDispatchResult:
    phone_number: str
    ttl_seconds: int
    resend_cooldown_seconds: int


@dataclass(slots=True)
class _FakeUser:
    id: UUID
    phone_number: str


@dataclass(slots=True)
class _FakeVerifyResult:
    user: _FakeUser
    is_new_user: bool


class _FakeAuthService:
    def __init__(self) -> None:
        self.register_calls: list[tuple[str, str | None]] = []
        self.resend_calls: list[tuple[str, str | None]] = []
        self.verify_calls: list[tuple[str, str]] = []
        self.register_error: Exception | None = None
        self.resend_error: Exception | None = None
        self.verify_error: Exception | None = None

    async def register(self, *, phone_number: str, ip_address: str | None) -> _FakeDispatchResult:
        self.register_calls.append((phone_number, ip_address))
        if self.register_error is not None:
            raise self.register_error
        return _FakeDispatchResult(
            phone_number=phone_number,
            ttl_seconds=600,
            resend_cooldown_seconds=60,
        )

    async def resend_verification_code(
        self,
        *,
        phone_number: str,
        ip_address: str | None,
    ) -> _FakeDispatchResult:
        self.resend_calls.append((phone_number, ip_address))
        if self.resend_error is not None:
            raise self.resend_error
        return _FakeDispatchResult(
            phone_number=phone_number,
            ttl_seconds=600,
            resend_cooldown_seconds=60,
        )

    async def verify_code(self, *, phone_number: str, code: str) -> _FakeVerifyResult:
        self.verify_calls.append((phone_number, code))
        if self.verify_error is not None:
            raise self.verify_error
        return _FakeVerifyResult(
            user=_FakeUser(
                id=UUID("00000000-0000-0000-0000-000000000123"),
                phone_number=phone_number,
            ),
            is_new_user=True,
        )


def test_register_returns_202_on_success() -> None:
    fake_service = _FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/register",
            json={"phone_number": "8 (999) 123-45-67"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json() == {
        "phone_number": "+79991234567",
        "ttl_seconds": 600,
        "resend_cooldown_seconds": 60,
    }
    assert fake_service.register_calls == [("+79991234567", "127.0.0.1")]


def test_register_returns_429_with_retry_after_header() -> None:
    fake_service = _FakeAuthService()
    fake_service.register_error = RateLimitExceededError(retry_after_seconds=60)
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/register",
            json={"phone_number": "79991234567"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.json()["detail"]["code"] == "rate_limit_exceeded"


def test_public_register_rejects_unknown_field_in_payload() -> None:
    fake_service = _FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "79991234567",
                "is_superuser": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert fake_service.register_calls == []


def test_verify_code_returns_200_on_success() -> None:
    fake_service = _FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: fake_service

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/verify-code",
            json={"phone_number": "8 (999) 123-45-67", "code": "123456"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "00000000-0000-0000-0000-000000000123",
        "phone_number": "+79991234567",
        "is_new_user": True,
    }
    assert fake_service.verify_calls == [("+79991234567", "123456")]


def test_verify_code_returns_400_for_invalid_code() -> None:
    fake_service = _FakeAuthService()
    fake_service.verify_error = InvalidVerificationCodeError(attempts_left=2)
    app.dependency_overrides[get_auth_service] = lambda: fake_service

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/verify-code",
            json={"phone_number": "79991234567", "code": "000000"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_verification_code"


def test_resend_verification_code_returns_202_on_success() -> None:
    fake_service = _FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/resend-verification-code",
            json={"phone_number": "8 (999) 123-45-67"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json() == {
        "phone_number": "+79991234567",
        "ttl_seconds": 600,
        "resend_cooldown_seconds": 60,
    }
    assert fake_service.resend_calls == [("+79991234567", "127.0.0.1")]


def test_resend_verification_code_returns_429_during_cooldown() -> None:
    fake_service = _FakeAuthService()
    fake_service.resend_error = VerificationCodeResendNotAllowedError(retry_after_seconds=45)
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/resend-verification-code",
            json={"phone_number": "79991234567"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "45"
    assert response.json()["detail"]["code"] == "verification_resend_not_allowed"
