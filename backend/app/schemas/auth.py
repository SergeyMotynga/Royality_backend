"""Схемы API-контрактов для auth-ручек."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.core.exceptions import InvalidPhoneNumberError
from backend.app.validators.auth import normalize_phone_number


class _PhoneSchema(BaseModel):
    """Базовая схема с номером телефона для auth-сценариев."""

    model_config = ConfigDict(extra="forbid")

    phone_number: str = Field(..., description="Номер телефона пользователя.")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        """Нормализует номер телефона и проверяет корректность формата."""
        try:
            return normalize_phone_number(value)
        except InvalidPhoneNumberError as error:
            raise ValueError(error.message) from error


class RegisterRequestSchema(_PhoneSchema):
    """Тело запроса на отправку OTP-кода подтверждения телефона."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "phone_number": "+79991234567",
            }
        },
    )


class RegisterResponseSchema(BaseModel):
    """Тело ответа после отправки OTP-кода."""

    model_config = ConfigDict(from_attributes=True)

    phone_number: str
    ttl_seconds: int
    resend_cooldown_seconds: int


class ResendVerificationCodeRequestSchema(_PhoneSchema):
    """Тело запроса повторной отправки OTP-кода."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "phone_number": "+79991234567",
            }
        },
    )


class ResendVerificationCodeResponseSchema(BaseModel):
    """Тело ответа после повторной отправки OTP-кода."""

    model_config = ConfigDict(from_attributes=True)

    phone_number: str
    ttl_seconds: int
    resend_cooldown_seconds: int


class VerifyCodeRequestSchema(_PhoneSchema):
    """Тело запроса подтверждения OTP-кода."""

    code: str = Field(..., min_length=6, max_length=6, description="Шестизначный OTP-код.")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "phone_number": "+79991234567",
                "code": "123456",
            }
        },
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        """Проверяет, что OTP-код состоит только из цифр."""
        if not value.isdigit():
            raise ValueError("Код подтверждения должен состоять только из цифр.")
        return value


class VerifyCodeResponseSchema(BaseModel):
    """Тело ответа после успешного подтверждения OTP-кода."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    phone_number: str
    is_new_user: bool

