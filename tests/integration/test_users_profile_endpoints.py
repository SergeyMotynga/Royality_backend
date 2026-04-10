"""Интеграционные тесты endpoint-ов профиля пользователя."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies.services import (
    get_auth_service,
    get_media_service,
    get_post_service,
    get_profile_service,
)
from backend.app.core.config import get_settings
from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.services.auth_service import AuthService
from backend.app.services.media_service import MediaService
from backend.app.services.post_service import PostService
from backend.app.services.profile_service import ProfileService


@pytest.fixture
def profile_context() -> tuple[TestClient, Session]:
    """Возвращает TestClient и in-memory сессию для profile-сценариев."""
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

    def override_get_profile_service() -> ProfileService:
        return ProfileService(
            user_crud=UserCrud(session=session),
            post_crud=PostCrud(session=session),
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
            _ = (content_type, payload)
            extension = "jpg"
            if file_name and "." in file_name:
                extension = file_name.rsplit(".", maxsplit=1)[1]
            return f"https://media.test/post/{user_id}/uploaded.{extension}"

        def upload_avatar_image(
            self,
            user_id: str,
            file_name: str | None,
            content_type: str | None,
            payload: bytes,
        ) -> str:
            _ = (content_type, payload)
            extension = "jpg"
            if file_name and "." in file_name:
                extension = file_name.rsplit(".", maxsplit=1)[1]
            return f"https://media.test/profile/{user_id}/avatar.{extension}"

    def override_get_media_service() -> MediaService:
        return TestMediaService()

    app.dependency_overrides[get_auth_service] = override_get_auth_service
    app.dependency_overrides[get_post_service] = override_get_post_service
    app.dependency_overrides[get_profile_service] = override_get_profile_service
    app.dependency_overrides[get_media_service] = override_get_media_service
    client = TestClient(app)
    try:
        yield client, session
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _signup_and_login(client: TestClient, login: str, name: str) -> tuple[str, str]:
    """Регистрирует пользователя и возвращает `(user_id, access_token)`."""
    password = "strong123"
    signup_response = client.post(
        "/api/v1/users/signup",
        json={"login": login, "password": password, "name": name},
    )
    login_response = client.post(
        "/api/v1/users/login",
        json={"login": login, "password": password},
    )
    return signup_response.json()["id"], login_response.json()["access_token"]


@pytest.mark.integration
def test_get_profile_by_id_returns_counts(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет получение профиля с подсчетом постов и подписчиков."""
    client, session = profile_context
    user_id, token = _signup_and_login(client, login=f"user_{uuid4().hex[:8]}", name="Игрок")
    follower_id, _ = _signup_and_login(client, login=f"user_{uuid4().hex[:8]}", name="Подписчик")

    client.post(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {token}"},
        data={"text": "Пост профиля", "disable_comments": "false"},
        files={"image": ("profile.jpg", b"profile-image", "image/jpeg")},
    )

    user_crud = UserCrud(session=session)
    user_crud.add_follower(follower_id=UUID(follower_id), followee_id=UUID(user_id))

    response = client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["nickname"] == "Игрок"
    assert payload["avatar_url"] is None
    assert payload["bio"] is None
    assert payload["level"] == 1
    assert payload["posts_count"] == 1
    assert payload["followers_count"] == 1
    assert payload["is_following"] is False


@pytest.mark.integration
def test_update_my_profile_success(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет успешное обновление профиля текущего пользователя."""
    client, _ = profile_context
    user_id, token = _signup_and_login(client, login=f"user_{uuid4().hex[:8]}", name="Игрок")
    headers = {"Authorization": f"Bearer {token}"}

    update_response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={
            "nickname": "Новый ник",
            "avatar_url": "https://example.com/new-avatar.png",
            "bio": "Текст обо мне",
            "level": 22,
        },
    )

    assert update_response.status_code == 200
    update_payload = update_response.json()
    assert update_payload["nickname"] == "Новый ник"
    assert update_payload["avatar_url"] == "https://example.com/new-avatar.png"
    assert update_payload["bio"] == "Текст обо мне"
    assert update_payload["level"] == 22
    assert update_payload["is_following"] is False

    get_response = client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["nickname"] == "Новый ник"
    assert get_payload["avatar_url"] == "https://example.com/new-avatar.png"
    assert get_payload["bio"] == "Текст обо мне"
    assert get_payload["level"] == 22
    assert get_payload["is_following"] is False


@pytest.mark.integration
def test_get_my_profile_success(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет получение профиля текущего пользователя по /users/me."""
    client, _ = profile_context
    user_id, token = _signup_and_login(client, login=f"user_{uuid4().hex[:8]}", name="Игрок")

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == user_id
    assert payload["nickname"] == "Игрок"
    assert payload["avatar_url"] is None
    assert payload["bio"] is None
    assert payload["level"] == 1
    assert payload["posts_count"] == 0
    assert payload["followers_count"] == 0
    assert payload["is_following"] is False


@pytest.mark.integration
def test_get_my_profile_requires_auth(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет, что /users/me недоступен без авторизации."""
    client, _ = profile_context

    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Требуется авторизация"}


@pytest.mark.integration
def test_upload_my_avatar_success(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет загрузку аватарки текущего пользователя."""
    client, _ = profile_context
    user_id, token = _signup_and_login(client, login=f"user_{uuid4().hex[:8]}", name="Игрок")

    response = client.post(
        "/api/v1/users/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": ("avatar.png", b"avatar-content", "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["url"] == f"https://media.test/profile/{user_id}/avatar.png"

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["avatar_url"] == f"https://media.test/profile/{user_id}/avatar.png"


@pytest.mark.integration
def test_get_profile_requires_auth(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет, что профиль пользователя недоступен без авторизации."""
    client, _ = profile_context
    user_id, _ = _signup_and_login(client, login=f"user_{uuid4().hex[:8]}", name="Игрок")

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Требуется авторизация"}


@pytest.mark.integration
def test_update_my_profile_validation_error(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет ошибку валидации при обновлении профиля."""
    client, _ = profile_context
    _, token = _signup_and_login(client, login=f"user_{uuid4().hex[:8]}", name="Игрок")

    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nickname": "Игрок",
            "avatar_url": "https://example.com/new-avatar.png",
            "bio": "Текст обо мне",
            "level": 0,
        },
    )

    assert response.status_code == 400


@pytest.mark.integration
def test_follow_and_unfollow_user(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет подписку и отписку от пользователя."""
    client, _ = profile_context
    target_user_id, _ = _signup_and_login(
        client,
        login=f"user_{uuid4().hex[:8]}",
        name="Цель подписки",
    )
    _, follower_token = _signup_and_login(
        client,
        login=f"user_{uuid4().hex[:8]}",
        name="Подписчик",
    )

    profile_before_follow = client.get(
        f"/api/v1/users/{target_user_id}",
        headers={"Authorization": f"Bearer {follower_token}"},
    )
    assert profile_before_follow.status_code == 200
    assert profile_before_follow.json()["followers_count"] == 0
    assert profile_before_follow.json()["is_following"] is False

    follow_response = client.post(
        f"/api/v1/users/{target_user_id}/follow",
        headers={"Authorization": f"Bearer {follower_token}"},
    )
    assert follow_response.status_code == 204

    profile_after_follow = client.get(
        f"/api/v1/users/{target_user_id}",
        headers={"Authorization": f"Bearer {follower_token}"},
    )
    assert profile_after_follow.status_code == 200
    assert profile_after_follow.json()["followers_count"] == 1
    assert profile_after_follow.json()["is_following"] is True

    unfollow_response = client.delete(
        f"/api/v1/users/{target_user_id}/follow",
        headers={"Authorization": f"Bearer {follower_token}"},
    )
    assert unfollow_response.status_code == 204

    profile_after_unfollow = client.get(
        f"/api/v1/users/{target_user_id}",
        headers={"Authorization": f"Bearer {follower_token}"},
    )
    assert profile_after_unfollow.status_code == 200
    assert profile_after_unfollow.json()["followers_count"] == 0
    assert profile_after_unfollow.json()["is_following"] is False


@pytest.mark.integration
def test_follow_self_returns_validation_error(profile_context: tuple[TestClient, Session]) -> None:
    """Проверяет ошибку подписки на самого себя."""
    client, _ = profile_context
    user_id, token = _signup_and_login(client, login=f"user_{uuid4().hex[:8]}", name="Игрок")

    response = client.post(
        f"/api/v1/users/{user_id}/follow",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
