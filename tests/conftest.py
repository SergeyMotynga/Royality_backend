"""Общие фикстуры для тестов проекта."""

from collections.abc import Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from tests.mocks.repositories import create_repository_mock


@pytest.fixture
def api_client() -> TestClient:
    """Возвращает тестовый HTTP-клиент приложения."""
    return TestClient(app)


@pytest.fixture
def repository_mock_factory() -> Any:
    """Возвращает фабрику для создания моков репозиториев."""

    def _factory(
        *,
        async_methods: Mapping[str, Any] | None = None,
        sync_methods: Mapping[str, Any] | None = None,
    ) -> Any:
        return create_repository_mock(
            async_methods=async_methods,
            sync_methods=sync_methods,
        )

    return _factory
