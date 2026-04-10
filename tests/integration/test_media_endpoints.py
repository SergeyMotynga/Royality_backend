"""Интеграционные тесты endpoint-а загрузки медиа."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies.services import get_auth_service, get_media_service
from backend.app.core.config import get_settings
from backend.app.crud.user_crud import UserCrud
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.services.auth_service import AuthService
from backend.app.services.media_service import MediaService


class FakeS3Client:
    """Фейковый S3-клиент для интеграционного теста."""

    def put_object(self, **kwargs: object) -> None:
        """Эмулирует успешную загрузку объекта."""


@pytest.fixture
def media_client() -> TestClient:
    """Возвращает TestClient с override зависимостей для media endpoint."""
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
            secret_key=get_settings().secret_key,
        )

    def override_get_media_service() -> MediaService:
        return MediaService(
            endpoint="localhost:9000",
            bucket_name="royality-media",
            region="us-east-1",
            secure=False,
            access_key="minio-user",
            secret_key="minio-password",
            public_endpoint="media.test",
            s3_client=FakeS3Client(),
        )

    app.dependency_overrides[get_auth_service] = override_get_auth_service
    app.dependency_overrides[get_media_service] = override_get_media_service
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _signup_and_login(client: TestClient, login: str, name: str) -> str:
    """Регистрирует пользователя и возвращает access token."""
    password = "strong123"
    client.post(
        "/api/v1/users/signup",
        json={"login": login, "password": password, "name": name},
    )
    response = client.post(
        "/api/v1/users/login",
        json={"login": login, "password": password},
    )
    return response.json()["access_token"]


@pytest.mark.integration
def test_media_upload_success(media_client: TestClient) -> None:
    """Проверяет успешную загрузку изображения через media endpoint."""
    token = _signup_and_login(media_client, login=f"user_{uuid4().hex[:8]}", name="Медиа")
    response = media_client.post(
        "/api/v1/media/upload?tag=post/temp",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("image.png", b"binary-content", "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["url"].startswith("http://media.test/royality-media/post/temp/")
    assert payload["url"].endswith(".png")


@pytest.mark.integration
def test_media_upload_rejects_non_image(media_client: TestClient) -> None:
    """Проверяет валидацию типа файла в media endpoint."""
    token = _signup_and_login(media_client, login=f"user_{uuid4().hex[:8]}", name="Медиа")
    response = media_client.post(
        "/api/v1/media/upload?tag=post/temp",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("notes.txt", b"text-content", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Допускаются только изображения"}
