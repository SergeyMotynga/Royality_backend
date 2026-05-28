"""Сервис профиля пользователя."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.models.user import User
from backend.app.validators.profile_validators import (
    validate_profile_avatar_url,
    validate_profile_bio,
    validate_profile_level,
    validate_profile_nickname,
)


class ProfileValidationError(ValueError):
    """Ошибка валидации данных профиля."""


class ProfileNotFoundError(ValueError):
    """Ошибка отсутствия профиля пользователя."""


@dataclass(frozen=True)
class ProfileResult:
    """DTO профиля пользователя."""

    id: UUID
    nickname: str
    avatar_url: str | None
    bio: str | None
    level: int
    posts_count: int
    followers_count: int
    is_following: bool
    created_at: datetime


class ProfileService:
    """Бизнес-логика чтения и изменения профиля пользователя."""

    def __init__(
        self,
        user_crud: UserCrud,
        post_crud: PostCrud,
        notification_service: object | None = None,
    ) -> None:
        self._user_crud = user_crud
        self._post_crud = post_crud
        self._notification_service = notification_service

    def get_profile(self, user_id: str, viewer_user_id: str) -> ProfileResult:
        """Возвращает профиль пользователя по идентификатору."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        parsed_viewer_user_id = self._parse_uuid(
            raw_uuid=viewer_user_id,
            field_name="пользователя",
        )
        user = self._user_crud.get_by_id(user_id=parsed_user_id)
        if user is None:
            raise ProfileNotFoundError("Профиль пользователя не найден")
        return self._build_profile_result(user=user, viewer_user_id=parsed_viewer_user_id)

    def update_my_profile(
        self,
        current_user_id: str,
        nickname: str,
        avatar_url: str | None,
        bio: str | None,
        level: int,
    ) -> ProfileResult:
        """Обновляет профиль текущего пользователя."""
        parsed_user_id = self._parse_uuid(raw_uuid=current_user_id, field_name="пользователя")
        user = self._user_crud.get_by_id(user_id=parsed_user_id)
        if user is None:
            raise ProfileNotFoundError("Профиль пользователя не найден")

        try:
            validate_profile_nickname(nickname=nickname)
            validate_profile_level(level=level)
            validate_profile_avatar_url(avatar_url=avatar_url)
            validate_profile_bio(bio=bio)
        except ValueError as exc:
            raise ProfileValidationError(str(exc)) from exc

        updated_user = self._user_crud.update_profile(
            user=user,
            nickname=nickname.strip(),
            avatar_url=avatar_url.strip() if avatar_url is not None else None,
            bio=bio,
            level=level,
        )
        return self._build_profile_result(user=updated_user, viewer_user_id=parsed_user_id)

    def update_my_avatar(self, current_user_id: str, avatar_url: str) -> None:
        """Обновляет аватар текущего пользователя."""
        parsed_user_id = self._parse_uuid(raw_uuid=current_user_id, field_name="пользователя")
        user = self._user_crud.get_by_id(user_id=parsed_user_id)
        if user is None:
            raise ProfileNotFoundError("Профиль пользователя не найден")

        try:
            validate_profile_avatar_url(avatar_url=avatar_url)
        except ValueError as exc:
            raise ProfileValidationError(str(exc)) from exc

        self._user_crud.update_avatar_url(user=user, avatar_url=avatar_url.strip())

    def follow_user(self, current_user_id: str, target_user_id: str) -> None:
        """Подписывает текущего пользователя на другого пользователя."""
        follower_id = self._parse_uuid(raw_uuid=current_user_id, field_name="пользователя")
        followee_id = self._parse_uuid(raw_uuid=target_user_id, field_name="пользователя")
        if follower_id == followee_id:
            raise ProfileValidationError("Нельзя подписаться на самого себя")

        follower = self._user_crud.get_by_id(user_id=follower_id)
        if follower is None:
            raise ProfileNotFoundError("Профиль пользователя не найден")
        followee = self._user_crud.get_by_id(user_id=followee_id)
        if followee is None:
            raise ProfileNotFoundError("Профиль пользователя не найден")

        created_relation = self._user_crud.add_follower(follower_id=follower_id, followee_id=followee_id)
        if created_relation:
            self._notify_user_followed(
                recipient_user_id=followee_id,
                actor_name=follower.name,
                actor_user_id=follower_id,
            )

    def unfollow_user(self, current_user_id: str, target_user_id: str) -> None:
        """Отписывает текущего пользователя от другого пользователя."""
        follower_id = self._parse_uuid(raw_uuid=current_user_id, field_name="пользователя")
        followee_id = self._parse_uuid(raw_uuid=target_user_id, field_name="пользователя")
        if follower_id == followee_id:
            raise ProfileValidationError("Нельзя отписаться от самого себя")

        follower = self._user_crud.get_by_id(user_id=follower_id)
        if follower is None:
            raise ProfileNotFoundError("Профиль пользователя не найден")
        followee = self._user_crud.get_by_id(user_id=followee_id)
        if followee is None:
            raise ProfileNotFoundError("Профиль пользователя не найден")

        self._user_crud.remove_follower(follower_id=follower_id, followee_id=followee_id)

    def _build_profile_result(self, user: User, viewer_user_id: UUID) -> ProfileResult:
        """Формирует DTO профиля из ORM-сущности пользователя."""
        posts_count = self._post_crud.count_posts_by_author(author_id=user.id)
        followers_count = self._user_crud.count_followers(user_id=user.id)
        is_following = self._user_crud.is_following(
            follower_id=viewer_user_id,
            followee_id=user.id,
        )
        return ProfileResult(
            id=user.id,
            nickname=user.name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            level=user.level,
            posts_count=posts_count,
            followers_count=followers_count,
            is_following=is_following,
            created_at=user.created_at,
        )

    def _parse_uuid(self, raw_uuid: str, field_name: str) -> UUID:
        """Приводит строковый идентификатор к UUID."""
        try:
            return UUID(raw_uuid)
        except ValueError as exc:
            raise ProfileValidationError(f"Некорректный идентификатор {field_name}") from exc

    def _notify_user_followed(self, recipient_user_id: UUID, actor_name: str, actor_user_id: UUID) -> None:
        """Отправляет push о подписке, если сервис уведомлений подключен."""
        if self._notification_service is None:
            return
        notify = getattr(self._notification_service, "notify_user_followed", None)
        if callable(notify):
            notify(
                recipient_user_id=recipient_user_id,
                actor_name=actor_name,
                actor_user_id=actor_user_id,
            )
