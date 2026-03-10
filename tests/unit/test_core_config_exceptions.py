from __future__ import annotations

import json

import pytest
from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import AppError, RateLimitExceededError, app_error_handler
from starlette.requests import Request

pytestmark = pytest.mark.unit


def test_settings_is_production_flag() -> None:
    assert Settings(ENV="prod").is_production
    assert not Settings(ENV="local").is_production


def test_get_settings_returns_cached_instance() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_settings_has_password_policy_fields() -> None:
    settings = Settings(PASSWORD_MIN_LENGTH=9, PASSWORD_MAX_LENGTH=30)

    assert settings.password_min_length == 9
    assert settings.password_max_length == 30


def test_settings_has_rate_limit_fields() -> None:
    settings = Settings(
        REGISTER_RATE_LIMIT_MAX_REQUESTS_PER_EMAIL=7,
        REGISTER_RATE_LIMIT_MAX_REQUESTS_PER_IP=40,
        REGISTER_RATE_LIMIT_WINDOW_SECONDS=1200,
        LOGIN_RATE_LIMIT_MAX_REQUESTS_PER_EMAIL=12,
        LOGIN_RATE_LIMIT_MAX_REQUESTS_PER_IP=80,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=1800,
        VERIFY_RATE_LIMIT_MAX_REQUESTS_PER_EMAIL=6,
        VERIFY_RATE_LIMIT_MAX_REQUESTS_PER_IP=35,
        VERIFY_RATE_LIMIT_WINDOW_SECONDS=700,
    )

    assert settings.register_rate_limit_max_requests_per_email == 7
    assert settings.register_rate_limit_max_requests_per_ip == 40
    assert settings.register_rate_limit_window_seconds == 1200
    assert settings.login_rate_limit_max_requests_per_email == 12
    assert settings.login_rate_limit_max_requests_per_ip == 80
    assert settings.login_rate_limit_window_seconds == 1800
    assert settings.verify_rate_limit_max_requests_per_email == 6
    assert settings.verify_rate_limit_max_requests_per_ip == 35
    assert settings.verify_rate_limit_window_seconds == 700


def test_app_error_allows_overrides() -> None:
    error = AppError("sample message", code="custom_code", status_code=418)

    assert error.message == "sample message"
    assert error.code == "custom_code"
    assert error.status_code == 418
    assert error.headers is None


def test_rate_limit_error_sets_retry_after_header() -> None:
    error = RateLimitExceededError(retry_after_seconds=120)

    assert error.headers == {"Retry-After": "120"}


@pytest.mark.asyncio
async def test_app_error_handler_includes_retry_after_header() -> None:
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    error = RateLimitExceededError(retry_after_seconds=60)

    response = await app_error_handler(request, error)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["detail"]["code"] == "rate_limit_exceeded"
