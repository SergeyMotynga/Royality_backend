"""Unit-тесты глобальных обработчиков исключений."""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.app.core.exceptions import register_exception_handlers


@pytest.mark.unit
def test_http_exception_handler_returns_json_response() -> None:
    """Проверяет формат ответа для HTTPException."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/http-error")
    async def raise_http_error() -> None:
        raise HTTPException(status_code=400, detail="Ошибка запроса")

    client = TestClient(app)
    response = client.get("/http-error")

    assert response.status_code == 400
    assert response.json() == {"detail": "Ошибка запроса"}


@pytest.mark.unit
def test_unexpected_exception_handler_returns_safe_message() -> None:
    """Проверяет безопасный ответ для непредвиденной ошибки."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/server-error")
    async def raise_unexpected_error() -> None:
        raise ValueError("hidden details")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/server-error")

    assert response.status_code == 500
    assert response.json() == {"detail": "Внутренняя ошибка сервера"}
