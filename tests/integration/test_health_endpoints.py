"""Интеграционные проверки health endpoint-ов."""

import pytest


@pytest.mark.integration
def test_root_health_endpoint(api_client) -> None:
    """Проверяет доступность корневого health endpoint."""
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scope": "root"}


@pytest.mark.integration
def test_public_health_endpoint(api_client) -> None:
    """Проверяет доступность публичного health endpoint в API v1."""
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scope": "public"}


@pytest.mark.integration
def test_admin_health_requires_superuser(api_client) -> None:
    """Проверяет, что admin health endpoint закрыт без роли администратора."""
    response = api_client.get("/api/v1/admin/health")
    assert response.status_code == 403
    assert response.json() == {"detail": "Недостаточно прав доступа"}


@pytest.mark.integration
def test_admin_health_for_superuser(api_client) -> None:
    """Проверяет доступность admin health endpoint при роли администратора."""
    response = api_client.get(
        "/api/v1/admin/health",
        headers={"X-Role": "admin", "X-User-Id": "admin-local-user"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "scope": "admin",
        "user_id": "admin-local-user",
    }
