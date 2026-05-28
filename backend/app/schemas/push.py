"""Pydantic-схемы для push-уведомлений."""

from pydantic import BaseModel


class PushTokenRequest(BaseModel):
    """Тело запроса регистрации FCM-токена устройства."""

    token: str
    platform: str
    device_id: str | None = None
