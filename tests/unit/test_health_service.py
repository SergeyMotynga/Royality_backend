"""Unit-тесты сервиса health-проверок."""

import pytest

from backend.app.services.health_service import build_health_payload


@pytest.mark.unit
def test_build_health_payload_without_user() -> None:
    """Проверяет payload без идентификатора пользователя."""
    payload = build_health_payload(scope="public")

    assert payload == {"status": "ok", "scope": "public"}


@pytest.mark.unit
def test_build_health_payload_with_user() -> None:
    """Проверяет payload с идентификатором пользователя."""
    payload = build_health_payload(scope="admin", user_id="admin-1")

    assert payload == {"status": "ok", "scope": "admin", "user_id": "admin-1"}
