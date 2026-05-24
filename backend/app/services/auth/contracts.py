"""Контракты зависимостей auth-сервиса."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from backend.app.models.refresh_session import RefreshSession
from backend.app.models.user import User


@dataclass(slots=True)
class AuthCodeState:
    """Состояние OTP-кода подтверждения телефона."""

    code: str
    attempts_left: int
    resend_available_at: int
    expires_at: int


class AuthRateLimiter(Protocol):
    """Контракт проверки лимитов auth-запросов через Redis."""

    async def check_auth_limits(self, *, phone_number: str, ip_address: str | None) -> None:
        """Проверяет лимиты и выбрасывает ошибку при превышении."""


class UserRepo(Protocol):
    """Контракт доступа к пользователям для auth-сервиса."""

    async def get_by_phone_number(self, phone_number: str) -> User | None:
        """Возвращает пользователя по номеру телефона."""

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Возвращает пользователя по идентификатору."""

    async def create_user(
        self,
        *,
        phone_number: str,
        is_verified: bool = False,
    ) -> User:
        """Создает пользователя и возвращает ORM-сущность."""

    async def mark_user_verified(self, *, user: User) -> User:
        """Помечает пользователя как верифицированного."""


class RefreshSessionRepo(Protocol):
    """Контракт хранения refresh-сессий пользователей."""

    async def create_session(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
    ) -> RefreshSession:
        """Создает refresh-сессию и возвращает ORM-сущность."""

    async def get_active_by_token_hash(self, *, token_hash: str) -> RefreshSession | None:
        """Возвращает активную refresh-сессию по хэшу токена."""

    async def get_active_by_id(self, *, session_id: UUID) -> RefreshSession | None:
        """Возвращает активную refresh-сессию по идентификатору."""

    async def revoke_session(self, *, refresh_session: RefreshSession) -> RefreshSession:
        """Отзывает refresh-сессию."""


class VerificationCodeStore(Protocol):
    """Контракт хранения OTP-кодов подтверждения телефона в Redis."""

    async def save_auth_code(
        self,
        *,
        phone_number: str,
        code: str,
        ttl_seconds: int,
        max_attempts: int,
        resend_cooldown_seconds: int,
    ) -> None:
        """Сохраняет код подтверждения и метаданные ограничений."""

    async def get_auth_code(self, *, phone_number: str) -> AuthCodeState | None:
        """Возвращает состояние OTP-кода по номеру телефона."""

    async def update_auth_code(
        self,
        *,
        phone_number: str,
        state: AuthCodeState,
    ) -> None:
        """Обновляет состояние OTP-кода по номеру телефона."""

    async def delete_auth_code(self, *, phone_number: str) -> None:
        """Удаляет состояние OTP-кода по номеру телефона."""


class SmsTaskPublisher(Protocol):
    """Контракт постановки задач отправки SMS-кодов подтверждения."""

    def enqueue_phone_verification(self, *, phone_number: str, code: str) -> None:
        """Ставит задачу отправки SMS-кода подтверждения."""
