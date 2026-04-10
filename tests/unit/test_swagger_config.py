"""Unit-тест конфигурации Swagger UI."""

import pytest

from backend.app.main import app


@pytest.mark.unit
def test_swagger_persist_authorization_enabled() -> None:
    """Проверяет, что Swagger сохраняет введенный токен авторизации."""
    assert app.swagger_ui_parameters.get("persistAuthorization") is True
