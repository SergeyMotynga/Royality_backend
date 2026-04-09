"""Утилиты для создания переиспользуемых моков репозиториев."""

from collections.abc import Mapping
from typing import Any
from unittest.mock import AsyncMock, MagicMock


def create_repository_mock(
    *,
    async_methods: Mapping[str, Any] | None = None,
    sync_methods: Mapping[str, Any] | None = None,
) -> MagicMock:
    """Создает мок репозитория с заданными sync/async методами."""
    repository = MagicMock()

    for method_name, return_value in (sync_methods or {}).items():
        method = MagicMock(name=method_name)
        method.return_value = return_value
        setattr(repository, method_name, method)

    for method_name, return_value in (async_methods or {}).items():
        method = AsyncMock(name=method_name)
        method.return_value = return_value
        setattr(repository, method_name, method)

    return repository
