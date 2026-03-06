import pytest
from backend.app.api.deps import get_current_user
from backend.app.main import app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


class _MockUser:
    def __init__(self, is_superuser: bool) -> None:
        self.is_superuser = is_superuser


def _superuser_override() -> _MockUser:
    return _MockUser(is_superuser=True)


def _regular_user_override() -> _MockUser:
    return _MockUser(is_superuser=False)


def test_public_healthcheck() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scope": "public"}


def test_root_healthcheck() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scope": "root"}


def test_admin_healthcheck_returns_501_without_auth_integration() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/admin/health")
    assert response.status_code == 501
    assert response.json()["detail"]["code"] == "auth_not_configured"


def test_admin_healthcheck_for_superuser() -> None:
    app.dependency_overrides[get_current_user] = _superuser_override

    try:
        client = TestClient(app)
        response = client.get("/api/v1/admin/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scope": "admin"}


def test_admin_healthcheck_for_regular_user() -> None:
    app.dependency_overrides[get_current_user] = _regular_user_override

    try:
        client = TestClient(app)
        response = client.get("/api/v1/admin/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"
