"""Исключения приложения и их обработчики для FastAPI."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Базовое исключение приложения с метаданными для ответа."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Инициализирует поля ошибки для API-ответа."""
        self.message = message
        self.headers = headers
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class PermissionDeniedError(AppError):
    """Ошибка недостатка прав доступа."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"

    def __init__(self, message: str = "Недостаточно прав доступа.") -> None:
        """Инициализирует ошибку недостатка прав."""
        super().__init__(message)


class AuthenticationNotConfiguredError(AppError):
    """Ошибка, когда слой аутентификации еще не подключен."""

    status_code = status.HTTP_501_NOT_IMPLEMENTED
    code = "auth_not_configured"

    def __init__(self, message: str = "Аутентификация пока не подключена.") -> None:
        """Инициализирует ошибку отсутствия подключенного auth-слоя."""
        super().__init__(message)


class EmailAlreadyRegisteredError(AppError):
    """Ошибка, когда email уже зарегистрирован в системе."""

    status_code = status.HTTP_409_CONFLICT
    code = "email_already_registered"

    def __init__(
        self,
        message: str = "Пользователь с таким email уже зарегистрирован.",
    ) -> None:
        """Инициализирует ошибку конфликта регистрации email."""
        super().__init__(message)


class WeakPasswordError(AppError):
    """Ошибка, когда пароль не прошел политику безопасности."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "weak_password"

    def __init__(
        self,
        message: str = "Пароль не соответствует требованиям безопасности.",
    ) -> None:
        """Инициализирует ошибку валидации пароля."""
        super().__init__(message)

    @classmethod
    def too_long(cls, *, max_length: int) -> WeakPasswordError:
        """Возвращает ошибку, если пароль превышает допустимую длину."""
        return cls(f"Пароль не должен быть длиннее {max_length} символов.")

    @classmethod
    def too_short(cls, *, min_length: int) -> WeakPasswordError:
        """Возвращает ошибку, если пароль короче допустимой длины."""
        return cls(f"Пароль не должен быть короче {min_length} символов.")

    @classmethod
    def contains_whitespace(cls) -> WeakPasswordError:
        """Возвращает ошибку, если пароль содержит пробелы."""
        return cls("Пароль не должен содержать пробелы.")

    @classmethod
    def missing_digit(cls) -> WeakPasswordError:
        """Возвращает ошибку, если пароль не содержит цифру."""
        return cls("Пароль должен содержать хотя бы одну цифру.")

    @classmethod
    def missing_special_symbol(cls) -> WeakPasswordError:
        """Возвращает ошибку, если пароль не содержит спецсимвол."""
        return cls("Пароль должен содержать хотя бы один спецсимвол.")


class RateLimitExceededError(AppError):
    """Ошибка превышения лимита частоты запросов."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limit_exceeded"

    def __init__(
        self,
        message: str = "Слишком много запросов. Попробуйте позже.",
        *,
        retry_after_seconds: int | None = None,
    ) -> None:
        """Инициализирует ошибку превышения лимита запросов."""
        headers: dict[str, str] | None = None
        if retry_after_seconds is not None:
            headers = {"Retry-After": str(retry_after_seconds)}
        super().__init__(message, headers=headers)


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Преобразует AppError в единый JSON-ответ API."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": {
                "code": exc.code,
                "message": exc.message,
            }
        },
        headers=exc.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики пользовательских исключений."""
    app.add_exception_handler(AppError, app_error_handler)
