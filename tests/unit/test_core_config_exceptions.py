import pytest
from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import AppError

pytestmark = pytest.mark.unit


def test_settings_is_production_flag() -> None:
    assert Settings(ENV="prod").is_production
    assert not Settings(ENV="local").is_production


def test_get_settings_returns_cached_instance() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_app_error_allows_overrides() -> None:
    error = AppError("sample message", code="custom_code", status_code=418)

    assert error.message == "sample message"
    assert error.code == "custom_code"
    assert error.status_code == 418
