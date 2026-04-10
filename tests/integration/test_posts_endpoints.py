"""Интеграционные тесты endpoint-ов постов."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies.services import (
    get_auth_service,
    get_media_service,
    get_post_service,
)
from backend.app.core.config import get_settings
from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.services.auth_service import AuthService
from backend.app.services.media_service import MediaService
from backend.app.services.post_service import PostService


@pytest.fixture
def posts_client() -> TestClient:
    """Возвращает TestClient с in-memory БД для сценариев постов."""
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

    def override_get_post_service() -> PostService:
        return PostService(
            post_crud=PostCrud(session=session),
            user_crud=UserCrud(session=session),
        )

    class TestMediaService(MediaService):
        """Фейковая медиа-служба для интеграционных тестов."""

        def __init__(self) -> None:
            pass

        def upload_post_image(
            self,
            user_id: str,
            file_name: str | None,
            content_type: str | None,
            payload: bytes,
        ) -> str:
            extension = "jpg"
            if file_name and "." in file_name:
                extension = file_name.rsplit(".", maxsplit=1)[1]
            return f"https://media.test/post/{user_id}/uploaded.{extension}"

    def override_get_media_service() -> MediaService:
        return TestMediaService()

    app.dependency_overrides[get_auth_service] = override_get_auth_service
    app.dependency_overrides[get_post_service] = override_get_post_service
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
    """Регистрирует пользователя и возвращает его access token."""
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
def test_create_post_and_get_post(posts_client: TestClient) -> None:
    """Проверяет создание поста и получение по идентификатору."""
    token = _signup_and_login(posts_client, login=f"user_{uuid4().hex[:8]}", name="Автор")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = posts_client.post(
        "/api/v1/posts",
        headers=headers,
        data={"text": "Первый пост", "disable_comments": "false"},
        files={"image": ("first.jpg", b"fake-jpg-content", "image/jpeg")},
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["text"] == "Первый пост"
    assert payload["medias"] == [f"https://media.test/post/{payload['author']['id']}/uploaded.jpg"]
    assert payload["likes_count"] == 0
    assert payload["author"]["name"] == "Автор"

    post_id = payload["id"]
    get_response = posts_client.get(f"/api/v1/posts/{post_id}", headers=headers)

    assert get_response.status_code == 200
    assert get_response.json()["id"] == post_id


@pytest.mark.integration
def test_feed_returns_posts_from_all_users(posts_client: TestClient) -> None:
    """Проверяет, что в ленту попадают посты разных пользователей."""
    token_a = _signup_and_login(posts_client, login=f"user_{uuid4().hex[:8]}", name="Автор A")
    token_b = _signup_and_login(posts_client, login=f"user_{uuid4().hex[:8]}", name="Автор B")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    posts_client.post(
        "/api/v1/posts",
        headers=headers_a,
        data={"text": "Пост A", "disable_comments": "false"},
        files={"image": ("a.jpg", b"image-a", "image/jpeg")},
    )
    posts_client.post(
        "/api/v1/posts",
        headers=headers_b,
        data={"text": "Пост B", "disable_comments": "false"},
        files={"image": ("b.jpg", b"image-b", "image/jpeg")},
    )

    response = posts_client.get("/api/v1/posts?limit=20&offset=0", headers=headers_a)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 2
    texts = [post["text"] for post in payload]
    assert "Пост A" in texts
    assert "Пост B" in texts


@pytest.mark.integration
def test_update_and_delete_post(posts_client: TestClient) -> None:
    """Проверяет редактирование и удаление поста автором."""
    token = _signup_and_login(posts_client, login=f"user_{uuid4().hex[:8]}", name="Автор")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = posts_client.post(
        "/api/v1/posts",
        headers=headers,
        data={"text": "Старый текст", "disable_comments": "false"},
        files={"image": ("old.jpg", b"old-image", "image/jpeg")},
    )
    post_id = create_response.json()["id"]

    update_response = posts_client.put(
        f"/api/v1/posts/{post_id}",
        headers=headers,
        json={
            "text": "Новый текст",
            "medias": ["https://example.com/new.jpg"],
            "disable_comments": True,
        },
    )

    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["text"] == "Новый текст"
    assert updated_payload["medias"] == ["https://example.com/new.jpg"]
    assert updated_payload["disable_comments"] is True

    delete_response = posts_client.delete(f"/api/v1/posts/{post_id}", headers=headers)
    assert delete_response.status_code == 204

    get_after_delete = posts_client.get(f"/api/v1/posts/{post_id}", headers=headers)
    assert get_after_delete.status_code == 404


@pytest.mark.integration
def test_like_and_unlike_post(posts_client: TestClient) -> None:
    """Проверяет лайк и снятие лайка у поста."""
    author_token = _signup_and_login(posts_client, login=f"user_{uuid4().hex[:8]}", name="Автор")
    liker_token = _signup_and_login(posts_client, login=f"user_{uuid4().hex[:8]}", name="Лайкер")
    author_headers = {"Authorization": f"Bearer {author_token}"}
    liker_headers = {"Authorization": f"Bearer {liker_token}"}

    create_response = posts_client.post(
        "/api/v1/posts",
        headers=author_headers,
        data={"text": "Пост для лайка", "disable_comments": "false"},
        files={"image": ("like.jpg", b"like-image", "image/jpeg")},
    )
    post_id = create_response.json()["id"]

    like_response = posts_client.post(f"/api/v1/posts/{post_id}/like", headers=liker_headers)
    assert like_response.status_code == 204

    get_after_like = posts_client.get(f"/api/v1/posts/{post_id}", headers=author_headers)
    assert get_after_like.status_code == 200
    assert get_after_like.json()["likes_count"] == 1

    unlike_response = posts_client.delete(f"/api/v1/posts/{post_id}/like", headers=liker_headers)
    assert unlike_response.status_code == 204

    get_after_unlike = posts_client.get(f"/api/v1/posts/{post_id}", headers=author_headers)
    assert get_after_unlike.status_code == 200
    assert get_after_unlike.json()["likes_count"] == 0
