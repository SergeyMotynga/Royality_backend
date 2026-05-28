"""Сервис регистрации FCM-токенов и отправки push-уведомлений."""

from dataclasses import dataclass
from uuid import UUID

from backend.app.crud.push_crud import PushDeviceTokenCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.services.firebase_push_client import FirebasePushClient


class PushValidationError(ValueError):
    """Ошибка валидации данных push-уведомлений."""


class PushNotFoundError(ValueError):
    """Ошибка отсутствия пользователя для push-операции."""


@dataclass(frozen=True)
class PushTokenResult:
    """DTO зарегистрированного FCM-токена."""

    token: str
    platform: str
    device_id: str | None


class PushNotificationService:
    """Бизнес-логика регистрации устройств и отправки событийных уведомлений."""

    def __init__(
        self,
        push_crud: PushDeviceTokenCrud,
        user_crud: UserCrud,
        fcm_client: FirebasePushClient,
    ) -> None:
        self._push_crud = push_crud
        self._user_crud = user_crud
        self._fcm_client = fcm_client

    def register_token(
        self,
        user_id: str,
        token: str,
        platform: str,
        device_id: str | None,
    ) -> PushTokenResult:
        """Регистрирует FCM-токен текущего пользователя."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        normalized_token = token.strip()
        normalized_platform = platform.strip().lower()
        normalized_device_id = device_id.strip() if device_id else None

        if not normalized_token:
            raise PushValidationError("FCM-токен не может быть пустым")
        if normalized_platform not in {"android", "ios"}:
            raise PushValidationError("Платформа push-токена должна быть android или ios")
        if self._user_crud.get_by_id(user_id=parsed_user_id) is None:
            raise PushNotFoundError("Пользователь не найден")

        saved_token = self._push_crud.upsert_token(
            user_id=parsed_user_id,
            token=normalized_token,
            platform=normalized_platform,
            device_id=normalized_device_id,
        )
        return PushTokenResult(
            token=saved_token.token,
            platform=saved_token.platform,
            device_id=saved_token.device_id,
        )

    def unregister_token(self, user_id: str, token: str) -> None:
        """Удаляет FCM-токен текущего пользователя."""
        parsed_user_id = self._parse_uuid(raw_uuid=user_id, field_name="пользователя")
        normalized_token = token.strip()
        if not normalized_token:
            raise PushValidationError("FCM-токен не может быть пустым")
        self._push_crud.delete_token(user_id=parsed_user_id, token=normalized_token)

    def notify_post_liked(self, recipient_user_id: UUID, actor_name: str, post_id: UUID) -> None:
        """Отправляет уведомление автору поста о лайке."""
        self._send_event(
            recipient_user_id=recipient_user_id,
            title="Новый лайк",
            body=f"{actor_name} лайкнул ваш пост",
            data={
                "type": "post_like",
                "post_id": str(post_id),
            },
        )

    def notify_post_commented(self, recipient_user_id: UUID, actor_name: str, post_id: UUID) -> None:
        """Отправляет уведомление автору поста о новом комментарии."""
        self._send_event(
            recipient_user_id=recipient_user_id,
            title="Новый комментарий",
            body=f"{actor_name} прокомментировал ваш пост",
            data={
                "type": "post_comment",
                "post_id": str(post_id),
            },
        )

    def notify_user_followed(self, recipient_user_id: UUID, actor_name: str, actor_user_id: UUID) -> None:
        """Отправляет уведомление пользователю о новом подписчике."""
        self._send_event(
            recipient_user_id=recipient_user_id,
            title="Новый подписчик",
            body=f"{actor_name} подписался на вас",
            data={
                "type": "user_follow",
                "user_id": str(actor_user_id),
            },
        )

    def _send_event(
        self,
        recipient_user_id: UUID,
        title: str,
        body: str,
        data: dict[str, str],
    ) -> None:
        """Отправляет уведомление на все устройства пользователя."""
        tokens = self._push_crud.list_tokens_by_user(user_id=recipient_user_id)
        result = self._fcm_client.send_to_tokens(tokens=tokens, title=title, body=body, data=data)
        if result.invalid_tokens:
            self._push_crud.delete_tokens(tokens=result.invalid_tokens)

    def _parse_uuid(self, raw_uuid: str, field_name: str) -> UUID:
        """Приводит строковый идентификатор к UUID."""
        try:
            return UUID(raw_uuid)
        except ValueError as exc:
            raise PushValidationError(f"Некорректный идентификатор {field_name}") from exc
