"""CRUD-операции для FCM-токенов устройств."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.push_device_token import PushDeviceToken


class PushDeviceTokenCrud:
    """Доступ к данным FCM-токенов устройств пользователей."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_token(
        self,
        user_id: UUID,
        token: str,
        platform: str,
        device_id: str | None,
    ) -> PushDeviceToken:
        """Создает или обновляет FCM-токен устройства."""
        stmt = select(PushDeviceToken).where(PushDeviceToken.token == token)
        existing = self._session.scalar(stmt)
        if existing is not None:
            existing.user_id = user_id
            existing.platform = platform
            existing.device_id = device_id
            self._session.add(existing)
            self._session.commit()
            self._session.refresh(existing)
            return existing

        device_token = PushDeviceToken(
            user_id=user_id,
            token=token,
            platform=platform,
            device_id=device_id,
        )
        self._session.add(device_token)
        self._session.commit()
        self._session.refresh(device_token)
        return device_token

    def delete_token(self, user_id: UUID, token: str) -> bool:
        """Удаляет FCM-токен текущего пользователя."""
        stmt = select(PushDeviceToken).where(
            PushDeviceToken.user_id == user_id,
            PushDeviceToken.token == token,
        )
        existing = self._session.scalar(stmt)
        if existing is None:
            return False
        self._session.delete(existing)
        self._session.commit()
        return True

    def list_tokens_by_user(self, user_id: UUID) -> list[str]:
        """Возвращает FCM-токены всех устройств пользователя."""
        stmt = select(PushDeviceToken.token).where(PushDeviceToken.user_id == user_id)
        return list(self._session.execute(stmt).scalars().all())

    def delete_tokens(self, tokens: list[str]) -> None:
        """Удаляет набор устаревших FCM-токенов."""
        if not tokens:
            return
        stmt = select(PushDeviceToken).where(PushDeviceToken.token.in_(tokens))
        for device_token in self._session.execute(stmt).scalars().all():
            self._session.delete(device_token)
        self._session.commit()
