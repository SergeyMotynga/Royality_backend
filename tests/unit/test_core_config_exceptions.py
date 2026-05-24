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


def test_settings_has_auth_code_policy_fields() -> None:
    settings = Settings(
        AUTH_CODE_TTL_SECONDS=700,
        AUTH_CODE_MAX_ATTEMPTS=6,
        AUTH_CODE_RESEND_COOLDOWN_SECONDS=90,
    )

    assert settings.auth_code_ttl_seconds == 700
    assert settings.auth_code_max_attempts == 6
    assert settings.auth_code_resend_cooldown_seconds == 90


def test_settings_has_rate_limit_fields() -> None:
    settings = Settings(
        AUTH_RATE_LIMIT_MAX_REQUESTS_PER_PHONE=7,
        AUTH_RATE_LIMIT_MAX_REQUESTS_PER_IP=40,
        AUTH_RATE_LIMIT_WINDOW_SECONDS=1200,
    )

    assert settings.auth_rate_limit_max_requests_per_phone == 7
    assert settings.auth_rate_limit_max_requests_per_ip == 40
    assert settings.auth_rate_limit_window_seconds == 1200


def test_settings_has_sms_provider_fields() -> None:
    settings = Settings(
        SMS_PROVIDER="mock",
        SMS_API_BASE_URL="https://sms.example.com",
        SMS_API_KEY="token",
        SMS_SENDER_ID="FINGURU",
    )

    assert settings.sms_provider == "mock"
    assert settings.sms_api_base_url == "https://sms.example.com"
    assert settings.sms_api_key == "token"
    assert settings.sms_sender_id == "FINGURU"


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
