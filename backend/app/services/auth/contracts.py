"""Контракты зависимостей auth-сервиса."""

from __future__ import annotations

from typing import Protocol

from backend.app.models.user import User


class RegisterRateLimiter(Protocol):
    """Контракт проверки лимитов регистрации через Redis."""

    async def check_register_limits(self, *, email: str, ip_address: str | None) -> None:
        """Проверяет лимиты регистрации и выбрасывает ошибку при превышении."""


class UserRepo(Protocol):
    """Контракт доступа к пользователям для auth-сервиса."""

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email."""

    async def create_user(self, *, email: str, password_hash: str) -> User:
        """Создает пользователя и возвращает ORM-сущность."""


class VerificationCodeStore(Protocol):
    """Контракт хранения кодов верификации email в Redis."""

    async def save_email_verification_code(
        self,
        *,
        email: str,
        code: str,
        ttl_seconds: int,
        max_attempts: int,
        resend_cooldown_seconds: int,
    ) -> None:
        """Сохраняет код верификации и метаданные ограничений."""


class EmailTaskPublisher(Protocol):
    """Контракт постановки задач отправки email в очередь воркера."""

    def enqueue_email_verification(self, *, email: str, code: str) -> None:
        """Ставит задачу отправки email-подтверждения."""
