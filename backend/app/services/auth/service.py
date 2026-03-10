"""Сервис авторизации и регистрации пользователей."""

from __future__ import annotations

import secrets

from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import EmailAlreadyRegisteredError
from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.services.auth.contracts import (
    EmailTaskPublisher,
    RegisterRateLimiter,
    UserRepo,
    VerificationCodeStore,
)


class AuthService:
    """Бизнес-логика регистрации и auth-сценариев."""

    def __init__(
        self,
        *,
        rate_limiter: RegisterRateLimiter,
        user_repo: UserRepo,
        verification_code_store: VerificationCodeStore,
        email_task_publisher: EmailTaskPublisher,
        settings: Settings | None = None,
    ) -> None:
        """Инициализирует зависимости auth-сервиса."""
        self.rate_limiter = rate_limiter
        self.user_repo = user_repo
        self.verification_code_store = verification_code_store
        self.email_task_publisher = email_task_publisher
        self.settings = settings or get_settings()

    async def register(self, *, email: str, password: str, ip_address: str | None) -> User:
        """Регистрирует пользователя, создает код верификации и ставит отправку письма в очередь."""
        normalized_email = self._normalize_email(email)

        await self.rate_limiter.check_register_limits(
            email=normalized_email,
            ip_address=ip_address,
        )

        existing_user = await self.user_repo.get_by_email(normalized_email)
        if existing_user is not None and existing_user.deleted_at is None:
            raise EmailAlreadyRegisteredError()

        password_hash = hash_password(password)
        created_user = await self.user_repo.create_user(
            email=normalized_email,
            password_hash=password_hash,
        )

        verification_code = self._generate_verification_code()
        await self.verification_code_store.save_email_verification_code(
            email=normalized_email,
            code=verification_code,
            ttl_seconds=self.settings.email_verification_code_ttl_seconds,
            max_attempts=self.settings.email_verification_max_attempts,
            resend_cooldown_seconds=self.settings.email_verification_resend_cooldown_seconds,
        )
        self.email_task_publisher.enqueue_email_verification(
            email=normalized_email,
            code=verification_code,
        )
        return created_user

    @staticmethod
    def _normalize_email(email: str) -> str:
        """Приводит email к нормализованному виду для хранения и поиска."""
        return email.strip().lower()

    @staticmethod
    def _generate_verification_code() -> str:
        """Генерирует шестизначный код подтверждения email."""
        return f"{secrets.randbelow(1_000_000):06d}"
