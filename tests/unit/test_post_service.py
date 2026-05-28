"""Unit-тесты сервиса постов."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.app.services.post_service import (
    PostCommentsDisabledError,
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
    user = SimpleNamespace(id=user_id, name="Тестовый автор", avatar_url=None)
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
    assert result.comments_count == 0
    assert result.is_liked is False


@pytest.mark.unit
def test_create_post_without_media_success(repository_mock_factory) -> None:
    """Проверяет успешное создание поста без изображений."""
    user_id = uuid4()
    created_at = datetime.now(UTC)
    user = SimpleNamespace(id=user_id, name="Тестовый автор")
    created_post = SimpleNamespace(
        id=uuid4(),
        text="Текст без картинки",
        disable_comments=False,
        created_at=created_at,
        author_id=user_id,
        author=user,
        medias=[],
    )

    user_crud = repository_mock_factory(sync_methods={"get_by_id": user})
    post_crud = repository_mock_factory(sync_methods={"create_post": created_post})
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    result = service.create_post(
        user_id=str(user_id),
        text="Текст без картинки",
        medias=[],
        disable_comments=False,
    )

    assert result.id == created_post.id
    assert result.text == "Текст без картинки"
    assert result.medias == []
    assert result.comments_count == 0


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


@pytest.mark.unit
def test_create_comment_success(repository_mock_factory) -> None:
    """Проверяет успешное создание комментария к посту."""
    user_id = uuid4()
    post_id = uuid4()
    created_at = datetime.now(UTC)
    user = SimpleNamespace(id=user_id, name="Комментатор", avatar_url=None)
    post = SimpleNamespace(id=post_id, author_id=user_id, disable_comments=False)
    comment = SimpleNamespace(
        id=uuid4(),
        post_id=post_id,
        author_id=user_id,
        author=user,
        text="Комментарий",
        created_at=created_at,
        updated_at=created_at,
    )

    user_crud = repository_mock_factory(sync_methods={"get_by_id": user})
    post_crud = repository_mock_factory(
        sync_methods={
            "get_post_by_id": post,
            "create_comment": comment,
        }
    )
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    result = service.create_comment(
        user_id=str(user_id),
        post_id=str(post_id),
        text="  Комментарий  ",
    )

    assert result.id == comment.id
    assert result.post_id == post_id
    assert result.text == "Комментарий"
    assert result.author.id == user_id
    post_crud.create_comment.assert_called_once_with(
        post_id=post_id,
        author_id=user_id,
        text="Комментарий",
    )


@pytest.mark.unit
def test_create_comment_for_disabled_post_forbidden(repository_mock_factory) -> None:
    """Проверяет запрет комментариев у поста с отключенными комментариями."""
    user_id = uuid4()
    post_id = uuid4()
    user = SimpleNamespace(id=user_id, name="Комментатор", avatar_url=None)
    post = SimpleNamespace(id=post_id, disable_comments=True)

    user_crud = repository_mock_factory(sync_methods={"get_by_id": user})
    post_crud = repository_mock_factory(sync_methods={"get_post_by_id": post})
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    with pytest.raises(PostCommentsDisabledError):
        service.create_comment(
            user_id=str(user_id),
            post_id=str(post_id),
            text="Комментарий",
        )


@pytest.mark.unit
def test_list_comments_success(repository_mock_factory) -> None:
    """Проверяет получение комментариев поста."""
    post_id = uuid4()
    author_id = uuid4()
    created_at = datetime.now(UTC)
    author = SimpleNamespace(id=author_id, name="Автор комментария", avatar_url=None)
    comment = SimpleNamespace(
        id=uuid4(),
        post_id=post_id,
        author_id=author_id,
        author=author,
        text="Первый",
        created_at=created_at,
        updated_at=created_at,
    )

    post_crud = repository_mock_factory(
        sync_methods={
            "get_post_by_id": SimpleNamespace(id=post_id),
            "list_comments": [comment],
        }
    )
    user_crud = repository_mock_factory()
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    result = service.list_comments(post_id=str(post_id), limit=50, offset=0)

    assert len(result) == 1
    assert result[0].text == "Первый"
    post_crud.list_comments.assert_called_once_with(post_id=post_id, limit=50, offset=0)


@pytest.mark.unit
def test_update_comment_forbidden_for_non_author(repository_mock_factory) -> None:
    """Проверяет запрет редактирования чужого комментария."""
    user_id = uuid4()
    author_id = uuid4()
    post_id = uuid4()
    created_at = datetime.now(UTC)
    comment = SimpleNamespace(
        id=uuid4(),
        post_id=post_id,
        author_id=author_id,
        author=SimpleNamespace(id=author_id, name="Автор", avatar_url=None),
        text="Старый текст",
        created_at=created_at,
        updated_at=created_at,
    )

    post_crud = repository_mock_factory(sync_methods={"get_comment_by_id": comment})
    user_crud = repository_mock_factory()
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    with pytest.raises(PostPermissionError):
        service.update_comment(
            user_id=str(user_id),
            post_id=str(post_id),
            comment_id=str(comment.id),
            text="Новый текст",
        )


@pytest.mark.unit
def test_delete_comment_success(repository_mock_factory) -> None:
    """Проверяет успешное удаление своего комментария."""
    user_id = uuid4()
    post_id = uuid4()
    created_at = datetime.now(UTC)
    comment = SimpleNamespace(
        id=uuid4(),
        post_id=post_id,
        author_id=user_id,
        author=SimpleNamespace(id=user_id, name="Автор", avatar_url=None),
        text="Комментарий",
        created_at=created_at,
        updated_at=created_at,
    )

    post_crud = repository_mock_factory(
        sync_methods={
            "get_comment_by_id": comment,
            "delete_comment": None,
        }
    )
    user_crud = repository_mock_factory()
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    service.delete_comment(
        user_id=str(user_id),
        post_id=str(post_id),
        comment_id=str(comment.id),
    )

    post_crud.delete_comment.assert_called_once_with(comment=comment)


@pytest.mark.unit
def test_get_post_contains_is_liked(repository_mock_factory) -> None:
    """Проверяет, что сервис возвращает признак лайка текущего пользователя."""
    viewer_id = uuid4()
    author_id = uuid4()
    post_id = uuid4()
    post = SimpleNamespace(
        id=post_id,
        text="Пост",
        disable_comments=False,
        created_at=datetime.now(UTC),
        author_id=author_id,
        author=SimpleNamespace(id=author_id, name="Автор", avatar_url="https://example.com/a.png"),
        medias=[SimpleNamespace(url="https://example.com/post.jpg")],
    )
    post_crud = repository_mock_factory(
        sync_methods={
            "get_post_by_id": post,
            "count_likes": 5,
            "is_liked": True,
        }
    )
    user_crud = repository_mock_factory()
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    result = service.get_post(post_id=str(post_id), viewer_user_id=str(viewer_id))

    assert result.id == post_id
    assert result.likes_count == 5
    assert result.is_liked is True
    assert result.author.avatar_url == "https://example.com/a.png"


@pytest.mark.unit
def test_get_feed_contains_is_liked_for_viewer(repository_mock_factory) -> None:
    """Проверяет, что в ленте учитывается признак лайка конкретного пользователя."""
    viewer_id = uuid4()
    author_id = uuid4()
    first_post_id = uuid4()
    second_post_id = uuid4()
    posts = [
        SimpleNamespace(
            id=first_post_id,
            text="Пост 1",
            disable_comments=False,
            created_at=datetime.now(UTC),
            author_id=author_id,
            author=SimpleNamespace(id=author_id, name="Автор", avatar_url=None),
            medias=[SimpleNamespace(url="https://example.com/1.jpg")],
        ),
        SimpleNamespace(
            id=second_post_id,
            text="Пост 2",
            disable_comments=False,
            created_at=datetime.now(UTC),
            author_id=author_id,
            author=SimpleNamespace(id=author_id, name="Автор", avatar_url=None),
            medias=[SimpleNamespace(url="https://example.com/2.jpg")],
        ),
    ]
    post_crud = repository_mock_factory(
        sync_methods={
            "list_feed": posts,
            "count_likes_for_posts": {
                first_post_id: 3,
                second_post_id: 1,
            },
            "get_liked_post_ids": {first_post_id},
        }
    )
    user_crud = repository_mock_factory()
    service = PostService(post_crud=post_crud, user_crud=user_crud)

    result = service.get_feed(limit=20, offset=0, viewer_user_id=str(viewer_id))

    assert len(result) == 2
    assert result[0].likes_count == 3
    assert result[0].is_liked is True
    assert result[1].likes_count == 1
    assert result[1].is_liked is False
