"""Unit-тесты сервиса постов."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.services.post_service import (
    PostNotFoundError,
    PostPermissionError,
    PostService,
    PostValidationError,
)


@pytest.mark.unit
def test_create_post_success(repository_mock_factory) -> None:
    """Проверяет успешное создание поста."""
    user_id = uuid4()
    created_at = datetime.now(UTC)
    user = SimpleNamespace(id=user_id, name="Тестовый автор")
    created_post = SimpleNamespace(
        id=uuid4(),
        text="Текст поста",
        disable_comments=False,
        created_at=created_at,
        author_id=user_id,
        author=user,
        medias=[SimpleNamespace(url="https://example.com/post.jpg")],
    )

    user_crud = repository_mock_factory(sync_methods={"get_by_id": user})
    post_crud = repository_mock_factory(sync_methods={"create_post": created_post})
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    result = service.create_post(
        user_id=str(user_id),
        text="Текст поста",
        medias=["https://example.com/post.jpg"],
        disable_comments=False,
    )

    assert result.id == created_post.id
    assert result.text == "Текст поста"
    assert result.medias == ["https://example.com/post.jpg"]
    assert result.author.id == user_id
    assert result.author.name == "Тестовый автор"
    assert result.likes_count == 0


@pytest.mark.unit
def test_create_post_validation_error(repository_mock_factory) -> None:
    """Проверяет ошибку валидации при создании поста."""
    user_crud = repository_mock_factory(sync_methods={"get_by_id": object()})
    post_crud = repository_mock_factory()
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    with pytest.raises(PostValidationError):
        service.create_post(user_id=str(uuid4()), text="", medias=[], disable_comments=False)


@pytest.mark.unit
def test_create_post_user_not_found(repository_mock_factory) -> None:
    """Проверяет ошибку при создании поста для отсутствующего пользователя."""
    post_crud = repository_mock_factory()
    user_crud = repository_mock_factory(sync_methods={"get_by_id": None})
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    with pytest.raises(PostNotFoundError, match="Пользователь не найден"):
        service.create_post(
            user_id=str(uuid4()),
            text="Текст поста",
            medias=["https://example.com/post.jpg"],
            disable_comments=False,
        )


@pytest.mark.unit
def test_update_post_forbidden_for_non_author(repository_mock_factory) -> None:
    """Проверяет запрет редактирования поста не автором."""
    user_id = uuid4()
    post = SimpleNamespace(
        id=uuid4(),
        text="Старый текст",
        disable_comments=False,
        created_at=datetime.now(UTC),
        author_id=uuid4(),
        author=SimpleNamespace(id=uuid4(), name="Автор"),
        medias=[SimpleNamespace(url="https://example.com/old.jpg")],
    )
    user_crud = repository_mock_factory(
        sync_methods={"get_by_id": SimpleNamespace(id=user_id, name="Редактор")}
    )
    post_crud = repository_mock_factory(sync_methods={"get_post_by_id": post})
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    with pytest.raises(PostPermissionError, match="Только автор может редактировать пост"):
        service.update_post(
            user_id=str(user_id),
            post_id=str(post.id),
            text="Новый текст",
            medias=["https://example.com/new.jpg"],
            disable_comments=True,
        )


@pytest.mark.unit
def test_delete_post_success(repository_mock_factory) -> None:
    """Проверяет успешное удаление поста автором."""
    user_id = uuid4()
    post = SimpleNamespace(
        id=uuid4(),
        author_id=user_id,
        author=SimpleNamespace(id=user_id, name="Автор"),
        medias=[],
        text="Текст",
        disable_comments=False,
        created_at=datetime.now(UTC),
    )
    user_crud = repository_mock_factory(
        sync_methods={"get_by_id": SimpleNamespace(id=user_id, name="Автор")}
    )
    post_crud = repository_mock_factory(sync_methods={"get_post_by_id": post, "delete_post": None})
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    service.delete_post(user_id=str(user_id), post_id=str(post.id))

    post_crud.delete_post.assert_called_once_with(post=post)
