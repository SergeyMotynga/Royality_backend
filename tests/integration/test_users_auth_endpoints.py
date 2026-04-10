"""Интеграционные тесты endpoint-ов регистрации и авторизации."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies.services import get_auth_service
from backend.app.crud.user_crud import UserCrud
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.services.auth_service import AuthService


@pytest.fixture
def auth_client() -> TestClient:
    """Возвращает TestClient с in-memory БД для auth-сценариев."""
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = session_factory()

    def override_get_auth_service() -> AuthService:
        return AuthService(
            user_crud=UserCrud(session=session),
            secret_key="integration-secret-key-32-characters",
        )

    app.dependency_overrides[get_auth_service] = override_get_auth_service
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.mark.integration
def test_signup_success(auth_client: TestClient) -> None:
    """Проверяет успешную регистрацию пользователя."""
    response = auth_client.post(
        "/api/v1/users/signup",
        json={"login": "new_user", "password": "strong123", "name": "Новый"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["login"] == "new_user"
    assert payload["name"] == "Новый"
    assert payload["id"]
    assert payload["created_at"]


@pytest.mark.integration
def test_signup_duplicate_login(auth_client: TestClient) -> None:
    """Проверяет ошибку регистрации с уже занятым логином."""
    auth_client.post(
        "/api/v1/users/signup",
        json={"login": "new_user", "password": "strong123", "name": "Новый"},
    )
    response = auth_client.post(
        "/api/v1/users/signup",
        json={"login": "new_user", "password": "strong123", "name": "Новый"},
    )

    assert response.status_code == 409


@pytest.mark.integration
def test_login_success(auth_client: TestClient) -> None:
    """Проверяет успешную авторизацию пользователя."""
    auth_client.post(
        "/api/v1/users/signup",
        json={"login": "new_user", "password": "strong123", "name": "Новый"},
    )
    response = auth_client.post(
        "/api/v1/users/login",
        json={"login": "new_user", "password": "strong123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.integration
def test_login_invalid_credentials(auth_client: TestClient) -> None:
    """Проверяет ошибку авторизации с неверным паролем."""
    auth_client.post(
        "/api/v1/users/signup",
        json={"login": "new_user", "password": "strong123", "name": "Новый"},
    )
    response = auth_client.post(
        "/api/v1/users/login",
        json={"login": "new_user", "password": "wrong123"},
    )

    assert response.status_code == 401
