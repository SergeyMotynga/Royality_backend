"""Сервис бизнес-логики постов."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.models.post import Post
from backend.app.models.post_comment import PostComment
from backend.app.validators.post_validators import (
    validate_comment_text,
    validate_comments_pagination,
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


class PostCommentsDisabledError(ValueError):
    """Ошибка запрета комментариев у поста."""


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
    comments_count: int
    is_liked: bool
    created_at: datetime


@dataclass(frozen=True)
class PostCommentResult:
    """Данные комментария к посту для отдачи в API-слой."""

    id: UUID
    post_id: UUID
    text: str
    author: PostAuthorResult
    created_at: datetime
    updated_at: datetime


class PostService:
    """Бизнес-логика постов и лайков."""

    def __init__(
        self,
        post_crud: PostCrud,
        user_crud: UserCrud,
        notification_service: object | None = None,
    ) -> None:
        self._post_crud = post_crud
        self._user_crud = user_crud
        self._notification_service = notification_service

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
            if normalized_medias:
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
        return self._build_post_result(
            post=post,
            likes_count=0,
            comments_count=0,
            is_liked=False,
        )

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
        comments_count = self._post_crud.count_comments(post_id=parsed_post_id)
        is_liked = self._post_crud.is_liked(post_id=parsed_post_id, user_id=parsed_viewer_user_id)
        return self._build_post_result(
            post=post,
            likes_count=likes_count,
            comments_count=comments_count,
            is_liked=is_liked,
        )

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
        comment_count_map = self._post_crud.count_comments_for_posts(post_ids=post_ids)
        liked_post_ids = self._post_crud.get_liked_post_ids(
            post_ids=post_ids,
            user_id=parsed_viewer_user_id,
        )
        return [
            self._build_post_result(
                post=post,
                likes_count=like_count_map.get(post.id, 0),
                comments_count=comment_count_map.get(post.id, 0),
                is_liked=post.id in liked_post_ids,
            )
            for post in posts
        ]

    def like_post(self, user_id: str, post_id: str) -> None:
        """Ставит лайк посту от имени пользователя."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")

        user = self._user_crud.get_by_id(parsed_user_id)
        if user is None:
            raise PostNotFoundError("Пользователь не найден")
        post = self._post_crud.get_post_by_id(post_id=parsed_post_id)
        if post is None:
            raise PostNotFoundError("Пост не найден")

        created_like = self._post_crud.add_like(post_id=parsed_post_id, user_id=parsed_user_id)
        if created_like and post.author_id != parsed_user_id:
            self._notify_post_liked(
                recipient_user_id=post.author_id,
                actor_name=user.name,
                post_id=post.id,
            )

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
            if normalized_medias:
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
        comments_count = self._post_crud.count_comments(post_id=updated_post.id)
        is_liked = self._post_crud.is_liked(post_id=updated_post.id, user_id=parsed_user_id)
        return self._build_post_result(
            post=updated_post,
            likes_count=likes_count,
            comments_count=comments_count,
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

    def create_comment(self, user_id: str, post_id: str, text: str) -> PostCommentResult:
        """Создает комментарий текущего пользователя к посту."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")
        try:
            validate_comment_text(text=text)
        except ValueError as exc:
            raise PostValidationError(str(exc)) from exc

        author = self._user_crud.get_by_id(parsed_user_id)
        if author is None:
            raise PostNotFoundError("Пользователь не найден")

        post = self._post_crud.get_post_by_id(post_id=parsed_post_id)
        if post is None:
            raise PostNotFoundError("Пост не найден")
        if post.disable_comments:
            raise PostCommentsDisabledError("Комментарии к этому посту отключены")

        comment = self._post_crud.create_comment(
            post_id=parsed_post_id,
            author_id=parsed_user_id,
            text=text.strip(),
        )
        if post.author_id != parsed_user_id:
            self._notify_post_commented(
                recipient_user_id=post.author_id,
                actor_name=author.name,
                post_id=post.id,
            )
        return self._build_comment_result(comment=comment)

    def list_comments(self, post_id: str, limit: int, offset: int) -> list[PostCommentResult]:
        """Возвращает комментарии поста."""
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")
        try:
            validate_comments_pagination(limit=limit, offset=offset)
        except ValueError as exc:
            raise PostValidationError(str(exc)) from exc

        if self._post_crud.get_post_by_id(post_id=parsed_post_id) is None:
            raise PostNotFoundError("Пост не найден")

        comments = self._post_crud.list_comments(
            post_id=parsed_post_id,
            limit=limit,
            offset=offset,
        )
        return [self._build_comment_result(comment=comment) for comment in comments]

    def update_comment(
        self,
        user_id: str,
        post_id: str,
        comment_id: str,
        text: str,
    ) -> PostCommentResult:
        """Обновляет комментарий автора."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")
        parsed_comment_id = self._parse_uuid(raw_uuid=comment_id, field_name="комментария")
        try:
            validate_comment_text(text=text)
        except ValueError as exc:
            raise PostValidationError(str(exc)) from exc

        comment = self._post_crud.get_comment_by_id(comment_id=parsed_comment_id)
        if comment is None or comment.post_id != parsed_post_id:
            raise PostNotFoundError("Комментарий не найден")
        if comment.author_id != parsed_user_id:
            raise PostPermissionError("Только автор может редактировать комментарий")

        updated_comment = self._post_crud.update_comment(comment=comment, text=text.strip())
        return self._build_comment_result(comment=updated_comment)

    def delete_comment(self, user_id: str, post_id: str, comment_id: str) -> None:
        """Удаляет комментарий автора."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_post_id = self._parse_uuid(raw_uuid=post_id, field_name="поста")
        parsed_comment_id = self._parse_uuid(raw_uuid=comment_id, field_name="комментария")

        comment = self._post_crud.get_comment_by_id(comment_id=parsed_comment_id)
        if comment is None or comment.post_id != parsed_post_id:
            raise PostNotFoundError("Комментарий не найден")
        if comment.author_id != parsed_user_id:
            raise PostPermissionError("Только автор может удалять комментарий")

        self._post_crud.delete_comment(comment=comment)

    def _parse_uuid(self, raw_uuid: str, field_name: str) -> UUID:
        """Приводит строковый идентификатор к UUID."""
        try:
            return UUID(raw_uuid)
        except ValueError as exc:
            raise PostValidationError(f"Некорректный идентификатор {field_name}") from exc

    def _build_post_result(
        self,
        post: Post,
        likes_count: int,
        comments_count: int,
        is_liked: bool,
    ) -> PostResult:
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
                avatar_url=getattr(post.author, "avatar_url", None),
            ),
            likes_count=likes_count,
            comments_count=comments_count,
            is_liked=is_liked,
            created_at=post.created_at,
        )

    def _build_comment_result(self, comment: PostComment) -> PostCommentResult:
        """Преобразует ORM-комментарий в DTO сервиса."""
        return PostCommentResult(
            id=comment.id,
            post_id=comment.post_id,
            text=comment.text,
            author=PostAuthorResult(
                id=comment.author.id,
                name=comment.author.name,
                avatar_url=getattr(comment.author, "avatar_url", None),
            ),
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    def _notify_post_liked(self, recipient_user_id: UUID, actor_name: str, post_id: UUID) -> None:
        """Отправляет push о лайке, если сервис уведомлений подключен."""
        if self._notification_service is None:
            return
        notify = getattr(self._notification_service, "notify_post_liked", None)
        if callable(notify):
            notify(recipient_user_id=recipient_user_id, actor_name=actor_name, post_id=post_id)

    def _notify_post_commented(self, recipient_user_id: UUID, actor_name: str, post_id: UUID) -> None:
        """Отправляет push о комментарии, если сервис уведомлений подключен."""
        if self._notification_service is None:
            return
        notify = getattr(self._notification_service, "notify_post_commented", None)
        if callable(notify):
            notify(recipient_user_id=recipient_user_id, actor_name=actor_name, post_id=post_id)
