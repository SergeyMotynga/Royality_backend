"""Клиент отправки push-уведомлений через Firebase Cloud Messaging."""

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PushSendResult:
    """Результат отправки push-уведомлений через FCM."""

    success_count: int
    failure_count: int
    invalid_tokens: list[str]


class FirebasePushClient:
    """Обертка над Firebase Admin SDK для отправки уведомлений."""

    def __init__(
        self,
        enabled: bool,
        credentials_path: str | None,
        credentials_json: str | None,
    ) -> None:
        self._enabled = enabled
        self._credentials_path = credentials_path
        self._credentials_json = credentials_json
        self._initialized = False

    def send_to_tokens(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, str],
    ) -> PushSendResult:
        """Отправляет одно уведомление на набор FCM-токенов."""
        if not tokens:
            return PushSendResult(success_count=0, failure_count=0, invalid_tokens=[])
        if not self._enabled:
            logger.info("FCM disabled, push notification skipped")
            return PushSendResult(success_count=0, failure_count=0, invalid_tokens=[])

        try:
            self._ensure_initialized()
            from firebase_admin import messaging

            messages = [
                messaging.Message(
                    token=token,
                    notification=messaging.Notification(title=title, body=body),
                    data=data,
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            channel_id="royality_events",
                            sound="default",
                        ),
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(sound="default"),
                        ),
                    ),
                )
                for token in tokens
            ]
            response = messaging.send_each(messages)
        except Exception:
            logger.exception("FCM push send failed before response")
            return PushSendResult(success_count=0, failure_count=len(tokens), invalid_tokens=[])

        invalid_tokens: list[str] = []
        for token, item in zip(tokens, response.responses, strict=False):
            if item.success:
                continue
            code = getattr(item.exception, "code", "") or ""
            if code in {"registration-token-not-registered", "invalid-argument"}:
                invalid_tokens.append(token)

        return PushSendResult(
            success_count=response.success_count,
            failure_count=response.failure_count,
            invalid_tokens=invalid_tokens,
        )

    def _ensure_initialized(self) -> None:
        """Лениво инициализирует Firebase Admin SDK."""
        if self._initialized:
            return

        from firebase_admin import credentials, get_app, initialize_app

        try:
            get_app()
        except ValueError:
            initialize_app(self._build_credentials(credentials_module=credentials))

        self._initialized = True

    def _build_credentials(self, credentials_module: Any) -> Any:
        """Создает Firebase credentials из JSON-строки или файла."""
        if self._credentials_json:
            return credentials_module.Certificate(json.loads(self._credentials_json))
        if self._credentials_path:
            return credentials_module.Certificate(self._credentials_path)
        raise RuntimeError("FCM включен, но Firebase credentials не настроены")
