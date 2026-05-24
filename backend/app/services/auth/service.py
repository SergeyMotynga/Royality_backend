"""Сервис регистрации и входа по номеру телефона и OTP-коду."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import (
    InvalidVerificationCodeError,
    VerificationCodeAttemptsExceededError,
    VerificationCodeExpiredError,
    VerificationCodeResendNotAllowedError,
)
from backend.app.models.user import User
from backend.app.services.auth.contracts import (
    AuthCodeState,
    AuthRateLimiter,
    SmsTaskPublisher,
    UserRepo,
    VerificationCodeStore,
)
from backend.app.validators.auth import normalize_phone_number


@dataclass(slots=True)
class AuthCodeDispatchResult:
    """Результат отправки OTP-кода подтверждения."""

    phone_number: str
    ttl_seconds: int
    resend_cooldown_seconds: int


@dataclass(slots=True)
class AuthVerifyResult:
    """Результат успешного подтверждения OTP-кода."""

    user: User
    is_new_user: bool


class AuthService:
    """Бизнес-логика OTP-регистрации/входа по номеру телефона."""

    def __init__(
        self,
        *,
        rate_limiter: AuthRateLimiter,
        user_repo: UserRepo,
        verification_code_store: VerificationCodeStore,
        sms_task_publisher: SmsTaskPublisher,
        settings: Settings | None = None,
    ) -> None:
        """Инициализирует зависимости auth-сервиса."""
        self.rate_limiter = rate_limiter
        self.user_repo = user_repo
        self.verification_code_store = verification_code_store
        self.sms_task_publisher = sms_task_publisher
        self.settings = settings or get_settings()

    async def register(self, *, phone_number: str, ip_address: str | None) -> AuthCodeDispatchResult:
        """Запрашивает OTP-код для номера телефона."""
        normalized_phone = normalize_phone_number(phone_number)
        await self.rate_limiter.check_auth_limits(
            phone_number=normalized_phone,
            ip_address=ip_address,
        )
        await self._issue_code(phone_number=normalized_phone)
        return AuthCodeDispatchResult(
            phone_number=normalized_phone,
            ttl_seconds=self.settings.auth_code_ttl_seconds,
            resend_cooldown_seconds=self.settings.auth_code_resend_cooldown_seconds,
        )

    async def resend_verification_code(
        self,
        *,
        phone_number: str,
        ip_address: str | None,
    ) -> AuthCodeDispatchResult:
        """Переотправляет OTP-код с учетом cooldown и rate-limit."""
        normalized_phone = normalize_phone_number(phone_number)
        current_state = await self.verification_code_store.get_auth_code(
            phone_number=normalized_phone
        )
        if current_state is not None:
            now = int(time.time())
            if now < current_state.resend_available_at:
                retry_after_seconds = current_state.resend_available_at - now
                raise VerificationCodeResendNotAllowedError(
                    retry_after_seconds=retry_after_seconds
                )

        await self.rate_limiter.check_auth_limits(
            phone_number=normalized_phone,
            ip_address=ip_address,
        )
        await self._issue_code(phone_number=normalized_phone)
        return AuthCodeDispatchResult(
            phone_number=normalized_phone,
            ttl_seconds=self.settings.auth_code_ttl_seconds,
            resend_cooldown_seconds=self.settings.auth_code_resend_cooldown_seconds,
        )

    async def verify_code(self, *, phone_number: str, code: str) -> AuthVerifyResult:
        """Проверяет OTP-код, регистрирует нового пользователя или авторизует существующего."""
        normalized_phone = normalize_phone_number(phone_number)
        current_state = await self.verification_code_store.get_auth_code(
            phone_number=normalized_phone
        )
        if current_state is None:
            raise VerificationCodeExpiredError()

        now = int(time.time())
        if now >= current_state.expires_at:
            await self.verification_code_store.delete_auth_code(phone_number=normalized_phone)
            raise VerificationCodeExpiredError()

        if code != current_state.code:
            await self._handle_invalid_code(
                phone_number=normalized_phone,
                state=current_state,
            )

        await self.verification_code_store.delete_auth_code(phone_number=normalized_phone)
        existing_user = await self.user_repo.get_by_phone_number(normalized_phone)
        if existing_user is None:
            created_user = await self.user_repo.create_user(
                phone_number=normalized_phone,
                is_verified=True,
            )
            return AuthVerifyResult(user=created_user, is_new_user=True)

        if not existing_user.is_verified:
            existing_user = await self.user_repo.mark_user_verified(user=existing_user)
        return AuthVerifyResult(user=existing_user, is_new_user=False)

    async def _handle_invalid_code(self, *, phone_number: str, state: AuthCodeState) -> None:
        """Обрабатывает неверный OTP-код и уменьшает счетчик попыток."""
        attempts_left = state.attempts_left - 1
        if attempts_left <= 0:
            await self.verification_code_store.delete_auth_code(phone_number=phone_number)
            raise VerificationCodeAttemptsExceededError()

        updated_state = AuthCodeState(
            code=state.code,
            attempts_left=attempts_left,
            resend_available_at=state.resend_available_at,
            expires_at=state.expires_at,
        )
        await self.verification_code_store.update_auth_code(
            phone_number=phone_number,
            state=updated_state,
        )
        raise InvalidVerificationCodeError(attempts_left=attempts_left)

    async def _issue_code(self, *, phone_number: str) -> None:
        """Генерирует и сохраняет OTP-код, затем ставит SMS-отправку в очередь."""
        code = self._generate_verification_code()
        await self.verification_code_store.save_auth_code(
            phone_number=phone_number,
            code=code,
            ttl_seconds=self.settings.auth_code_ttl_seconds,
            max_attempts=self.settings.auth_code_max_attempts,
            resend_cooldown_seconds=self.settings.auth_code_resend_cooldown_seconds,
        )
        self.sms_task_publisher.enqueue_phone_verification(
            phone_number=phone_number,
            code=code,
        )

    @staticmethod
    def _generate_verification_code() -> str:
        """Генерирует шестизначный OTP-код подтверждения."""
        return f"{secrets.randbelow(1_000_000):06d}"

