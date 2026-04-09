"""Глобальные обработчики исключений FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует стандартные обработчики ошибок приложения."""

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Возвращает стандартизированный ответ для HTTP-ошибок."""
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        _request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        """Возвращает безопасный ответ для непредвиденных ошибок."""
        return JSONResponse(
            status_code=500,
            content={"detail": "Внутренняя ошибка сервера"},
        )
