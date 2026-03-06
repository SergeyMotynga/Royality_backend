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
    ) -> None:
        """Инициализирует поля ошибки для API-ответа."""
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class PermissionDeniedError(AppError):
    """Ошибка недостатка прав доступа."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"


class AuthenticationNotConfiguredError(AppError):
    """Ошибка, когда слой аутентификации еще не подключен."""

    status_code = status.HTTP_501_NOT_IMPLEMENTED
    code = "auth_not_configured"


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
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики пользовательских исключений."""
    app.add_exception_handler(AppError, app_error_handler)
