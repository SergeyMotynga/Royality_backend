"""Unit-тесты сервиса профиля пользователя."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.services.profile_service import (
    ProfileNotFoundError,
    ProfileService,
    ProfileValidationError,
)


@pytest.mark.unit
def test_get_profile_success(repository_mock_factory) -> None:
    """Проверяет успешное получение профиля пользователя."""
    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        name="Игрок",
        avatar_url="https://example.com/avatar.png",
        bio="Обо мне",
        level=12,
        created_at=datetime.now(UTC),
    )
    user_crud = repository_mock_factory(
        sync_methods={
            "get_by_id": user,
            "count_followers": 3,
            "is_following": True,
        }
    )
    post_crud = repository_mock_factory(sync_methods={"count_posts_by_author": 7})
    service = ProfileService(user_crud=user_crud, post_crud=post_crud)

    result = service.get_profile(user_id=str(user_id), viewer_user_id=str(uuid4()))

    assert result.id == user_id
    assert result.nickname == "Игрок"
    assert result.avatar_url == "https://example.com/avatar.png"
    assert result.bio == "Обо мне"
    assert result.level == 12
    assert result.posts_count == 7
    assert result.followers_count == 3
    assert result.is_following is True


@pytest.mark.unit
def test_get_profile_not_found(repository_mock_factory) -> None:
    """Проверяет ошибку получения отсутствующего профиля."""
    user_crud = repository_mock_factory(sync_methods={"get_by_id": None})
    post_crud = repository_mock_factory()
    service = ProfileService(user_crud=user_crud, post_crud=post_crud)

    with pytest.raises(ProfileNotFoundError, match="Профиль пользователя не найден"):
        service.get_profile(user_id=str(uuid4()), viewer_user_id=str(uuid4()))


@pytest.mark.unit
def test_update_my_profile_success(repository_mock_factory) -> None:
    """Проверяет успешное обновление профиля текущего пользователя."""
    user_id = uuid4()
    initial_user = SimpleNamespace(
        id=user_id,
        name="Старый ник",
        avatar_url=None,
        bio=None,
        level=1,
        created_at=datetime.now(UTC),
    )
    updated_user = SimpleNamespace(
        id=user_id,
        name="Новый ник",
        avatar_url="https://example.com/new.png",
        bio="Новый текст обо мне",
        level=20,
        created_at=initial_user.created_at,
    )
    user_crud = repository_mock_factory(
        sync_methods={
            "get_by_id": initial_user,
            "update_profile": updated_user,
            "count_followers": 4,
            "is_following": False,
        }
    )
    post_crud = repository_mock_factory(sync_methods={"count_posts_by_author": 11})
    service = ProfileService(user_crud=user_crud, post_crud=post_crud)

    result = service.update_my_profile(
        current_user_id=str(user_id),
        nickname="Новый ник",
        avatar_url="https://example.com/new.png",
        bio="Новый текст обо мне",
        level=20,
    )

    assert result.nickname == "Новый ник"
    assert result.level == 20
    assert result.posts_count == 11
    assert result.followers_count == 4
    assert result.is_following is False


@pytest.mark.unit
def test_update_my_profile_validation_error(repository_mock_factory) -> None:
    """Проверяет ошибку валидации при обновлении профиля."""
    user_crud = repository_mock_factory(
        sync_methods={
            "get_by_id": object(),
        }
    )
    post_crud = repository_mock_factory()
    service = ProfileService(user_crud=user_crud, post_crud=post_crud)

    with pytest.raises(ProfileValidationError):
        service.update_my_profile(
            current_user_id=str(uuid4()),
            nickname="A",
            avatar_url="https://example.com/avatar.png",
            bio="bio",
            level=1,
        )


@pytest.mark.unit
def test_follow_user_success(repository_mock_factory) -> None:
    """Проверяет успешную подписку на пользователя."""
    current_user_id = uuid4()
    target_user_id = uuid4()
    user_crud = repository_mock_factory(
        sync_methods={
            "get_by_id": SimpleNamespace(),
            "add_follower": True,
        }
    )
    post_crud = repository_mock_factory()
    service = ProfileService(user_crud=user_crud, post_crud=post_crud)

    service.follow_user(current_user_id=str(current_user_id), target_user_id=str(target_user_id))

    user_crud.add_follower.assert_called_once_with(
        follower_id=current_user_id,
        followee_id=target_user_id,
    )


@pytest.mark.unit
def test_follow_user_to_self_validation_error(repository_mock_factory) -> None:
    """Проверяет ошибку подписки на самого себя."""
    user_id = uuid4()
    user_crud = repository_mock_factory(sync_methods={"get_by_id": SimpleNamespace()})
    post_crud = repository_mock_factory()
    service = ProfileService(user_crud=user_crud, post_crud=post_crud)

    with pytest.raises(ProfileValidationError, match="Нельзя подписаться на самого себя"):
        service.follow_user(current_user_id=str(user_id), target_user_id=str(user_id))


@pytest.mark.unit
def test_unfollow_user_success(repository_mock_factory) -> None:
    """Проверяет успешную отписку от пользователя."""
    current_user_id = uuid4()
    target_user_id = uuid4()
    user_crud = repository_mock_factory(
        sync_methods={
            "get_by_id": SimpleNamespace(),
            "remove_follower": True,
        }
    )
    post_crud = repository_mock_factory()
    service = ProfileService(user_crud=user_crud, post_crud=post_crud)

    service.unfollow_user(current_user_id=str(current_user_id), target_user_id=str(target_user_id))

    user_crud.remove_follower.assert_called_once_with(
        follower_id=current_user_id,
        followee_id=target_user_id,
    )


@pytest.mark.unit
def test_update_my_avatar_success(repository_mock_factory) -> None:
    """Проверяет успешное обновление аватарки текущего пользователя."""
    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        name="Игрок",
        avatar_url=None,
        bio=None,
        level=1,
        created_at=datetime.now(UTC),
    )
    user_crud = repository_mock_factory(
        sync_methods={
            "get_by_id": user,
            "update_avatar_url": user,
        }
    )
    post_crud = repository_mock_factory()
    service = ProfileService(user_crud=user_crud, post_crud=post_crud)

    service.update_my_avatar(
        current_user_id=str(user_id),
        avatar_url="https://example.com/avatar.png",
    )

    user_crud.update_avatar_url.assert_called_once_with(
        user=user,
        avatar_url="https://example.com/avatar.png",
    )
