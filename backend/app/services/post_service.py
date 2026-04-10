"""Сервис бизнес-логики постов."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.models.post import Post
from backend.app.validators.post_validators import (
    validate_post_medias,
    validate_post_text,
    validate_posts_pagination,
)


class PostValidationError(ValueError):
    """Ошибка валидации входных данных поста."""


class PostNotFoundError(ValueError):
    """Ошибка отсутствия связанной сущности поста."""


class PostPermissionError(ValueError):
    """Ошибка отсутствия прав на изменение поста."""


@dataclass(frozen=True)
class PostAuthorResult:
    """Автор поста для ответа API."""

    id: UUID
    name: str
    avatar_url: str | None


@dataclass(frozen=True)
class PostResult:
    """Данные поста для отдачи в API-слой."""

    id: UUID
    text: str
    medias: list[str]
    disable_comments: bool
    author: PostAuthorResult
    likes_count: int
    is_liked: bool
    created_at: datetime


class PostService:
    """Бизнес-логика постов и лайков."""

    def __init__(self, post_crud: PostCrud, user_crud: UserCrud) -> None:
        self._post_crud = post_crud
        self._user_crud = user_crud

    def create_post(
        self,
        user_id: str,
        text: str,
        medias: list[str],
        disable_comments: bool,
    ) -> PostResult:
        """Создает новый пост автора."""
        author_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        normalized_medias = [media.strip() for media in medias]
        try:
            validate_post_text(text=text)
            validate_post_medias(medias=normalized_medias)
        except ValueError as exc:
            raise PostValidationError(str(exc)) from exc

        author = self._user_crud.get_by_id(author_id)
        if author is None:
            raise PostNotFoundError("Пользователь не найден")

        post = self._post_crud.create_post(
            author_id=author_id,
            text=text.strip(),
            medias=normalized_medias,
            disable_comments=disable_comments,
        )
        return self._build_post_result(post=post, likes_count=0, is_liked=False)

    def get_post(self, post_id: str, viewer_user_id: str) -> PostResult:
        """Возвращает пост по идентификатору."""
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")
        parsed_viewer_user_id = self._parse_uuid(
            raw_uuid=viewer_user_id,
            field_name="пользователя",
        )
        post = self._post_crud.get_post_by_id(post_id=parsed_post_id)
        if post is None:
            raise PostNotFoundError("Пост не найден")
        likes_count = self._post_crud.count_likes(post_id=parsed_post_id)
        is_liked = self._post_crud.is_liked(post_id=parsed_post_id, user_id=parsed_viewer_user_id)
        return self._build_post_result(post=post, likes_count=likes_count, is_liked=is_liked)

    def get_feed(self, limit: int, offset: int, viewer_user_id: str) -> list[PostResult]:
        """Возвращает ленту постов."""
        parsed_viewer_user_id = self._parse_uuid(
            raw_uuid=viewer_user_id,
            field_name="пользователя",
        )
        try:
            validate_posts_pagination(limit=limit, offset=offset)
        except ValueError as exc:
            raise PostValidationError(str(exc)) from exc

        posts = self._post_crud.list_feed(limit=limit, offset=offset)
        post_ids = [post.id for post in posts]
        like_count_map = self._post_crud.count_likes_for_posts(post_ids=post_ids)
        liked_post_ids = self._post_crud.get_liked_post_ids(
            post_ids=post_ids,
            user_id=parsed_viewer_user_id,
        )
        return [
            self._build_post_result(
                post=post,
                likes_count=like_count_map.get(post.id, 0),
                is_liked=post.id in liked_post_ids,
            )
            for post in posts
        ]

    def like_post(self, user_id: str, post_id: str) -> None:
        """Ставит лайк посту от имени пользователя."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")

        if self._user_crud.get_by_id(parsed_user_id) is None:
            raise PostNotFoundError("Пользователь не найден")
        if self._post_crud.get_post_by_id(post_id=parsed_post_id) is None:
            raise PostNotFoundError("Пост не найден")

        self._post_crud.add_like(post_id=parsed_post_id, user_id=parsed_user_id)

    def unlike_post(self, user_id: str, post_id: str) -> None:
        """Снимает лайк поста от имени пользователя."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")

        if self._user_crud.get_by_id(parsed_user_id) is None:
            raise PostNotFoundError("Пользователь не найден")
        if self._post_crud.get_post_by_id(post_id=parsed_post_id) is None:
            raise PostNotFoundError("Пост не найден")

        self._post_crud.remove_like(post_id=parsed_post_id, user_id=parsed_user_id)

    def update_post(
        self,
        user_id: str,
        post_id: str,
        text: str,
        medias: list[str],
        disable_comments: bool,
    ) -> PostResult:
        """Обновляет пост автора."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")
        normalized_medias = [media.strip() for media in medias]
        try:
            validate_post_text(text=text)
            validate_post_medias(medias=normalized_medias)
        except ValueError as exc:
            raise PostValidationError(str(exc)) from exc

        if self._user_crud.get_by_id(parsed_user_id) is None:
            raise PostNotFoundError("Пользователь не найден")

        post = self._post_crud.get_post_by_id(post_id=parsed_post_id)
        if post is None:
            raise PostNotFoundError("Пост не найден")
        if post.author_id != parsed_user_id:
            raise PostPermissionError("Только автор может редактировать пост")

        updated_post = self._post_crud.update_post(
            post=post,
            text=text.strip(),
            medias=normalized_medias,
            disable_comments=disable_comments,
        )
        likes_count = self._post_crud.count_likes(post_id=updated_post.id)
        is_liked = self._post_crud.is_liked(post_id=updated_post.id, user_id=parsed_user_id)
        return self._build_post_result(
            post=updated_post,
            likes_count=likes_count,
            is_liked=is_liked,
        )

    def delete_post(self, user_id: str, post_id: str) -> None:
        """Удаляет пост автора."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")

        if self._user_crud.get_by_id(parsed_user_id) is None:
            raise PostNotFoundError("Пользователь не найден")

        post = self._post_crud.get_post_by_id(post_id=parsed_post_id)
        if post is None:
            raise PostNotFoundError("Пост не найден")
        if post.author_id != parsed_user_id:
            raise PostPermissionError("Только автор может удалять пост")

        self._post_crud.delete_post(post=post)

    def _parse_uuid(self, raw_uuid: str, field_name: str) -> UUID:
        """Приводит строковый идентификатор к UUID."""
        try:
            return UUID(raw_uuid)
        except ValueError as exc:
            raise PostValidationError(f"Некорректный идентификатор {field_name}") from exc

    def _build_post_result(self, post: Post, likes_count: int, is_liked: bool) -> PostResult:
        """Преобразует ORM-сущность в DTO сервиса."""
        media_urls = [media.url for media in post.medias]
        return PostResult(
            id=post.id,
            text=post.text,
            medias=media_urls,
            disable_comments=post.disable_comments,
            author=PostAuthorResult(
                id=post.author.id,
                name=post.author.name,
                avatar_url=post.author.avatar_url,
            ),
            likes_count=likes_count,
            is_liked=is_liked,
            created_at=post.created_at,
        )
