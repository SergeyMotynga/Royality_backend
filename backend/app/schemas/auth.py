"""Схемы API-контрактов для auth-ручек."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from backend.app.core.exceptions import WeakPasswordError
from backend.app.core.security import (
    DEFAULT_PASSWORD_MAX_LENGTH,
    DEFAULT_PASSWORD_MIN_LENGTH,
    validate_password_policy,
)


class RegisterRequestSchema(BaseModel):
    """Тело запроса регистрации пользователя."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "valid_pass1!",
            }
        },
    )

    email: EmailStr = Field(..., description="Email пользователя.")
    password: str = Field(
        ...,
        min_length=DEFAULT_PASSWORD_MIN_LENGTH,
        max_length=DEFAULT_PASSWORD_MAX_LENGTH,
        description=(
            "Пароль пользователя. Требования: 8-26 символов, минимум одна цифра, "
            "минимум один спецсимвол, без пробелов."
        ),
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        """Обрезает пробелы вокруг email до форматной валидации."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Проверяет пароль по политике безопасности на входе API."""
        try:
            validate_password_policy(
                value,
                min_length=DEFAULT_PASSWORD_MIN_LENGTH,
                max_length=DEFAULT_PASSWORD_MAX_LENGTH,
            )
        except WeakPasswordError as error:
            raise ValueError(error.message) from error
        return value


class RegisterResponseSchema(BaseModel):
    """Тело ответа при успешной регистрации."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
