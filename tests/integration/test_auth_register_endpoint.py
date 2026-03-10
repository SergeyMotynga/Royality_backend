from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import pytest
from backend.app.api.v1.endpoints.public.auth import get_auth_service, get_client_ip
from backend.app.core.exceptions import (
    EmailAlreadyRegisteredError,
    RateLimitExceededError,
    WeakPasswordError,
)
from backend.app.main import app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@dataclass(slots=True)
class _FakeUser:
    id: UUID
    email: str


class _FakeAuthService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []
        self.should_raise: Exception | None = None

    async def register(self, *, email: str, password: str, ip_address: str | None) -> _FakeUser:
        self.calls.append((email, password, ip_address))
        if self.should_raise is not None:
            raise self.should_raise

        return _FakeUser(
            id=UUID("00000000-0000-0000-0000-000000000123"),
            email=email.strip().lower(),
        )


def test_register_returns_201_on_success() -> None:
    fake_service = _FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "  NewUser@Example.COM ", "password": "valid_pass1!"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "id": "00000000-0000-0000-0000-000000000123",
        "email": "newuser@example.com",
    }
    assert fake_service.calls == [("NewUser@example.com", "valid_pass1!", "127.0.0.1")]


def test_register_returns_409_if_email_already_exists() -> None:
    fake_service = _FakeAuthService()
    fake_service.should_raise = EmailAlreadyRegisteredError()
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "exists@example.com", "password": "valid_pass1!"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "email_already_registered"


def test_register_returns_429_with_retry_after_header() -> None:
    fake_service = _FakeAuthService()
    fake_service.should_raise = RateLimitExceededError(retry_after_seconds=60)
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": "valid_pass1!"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.json()["detail"]["code"] == "rate_limit_exceeded"


def test_register_returns_422_for_weak_password_error() -> None:
    fake_service = _FakeAuthService()
    fake_service.should_raise = WeakPasswordError.missing_digit()
    app.dependency_overrides[get_auth_service] = lambda: fake_service
    app.dependency_overrides[get_client_ip] = lambda: "127.0.0.1"

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": "valid_pass1!"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "weak_password"
