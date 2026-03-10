"""Общие зависимости для HTTP-endpoint-ов."""

from __future__ import annotations

from typing import Annotated, Protocol

from fastapi import Depends

from backend.app.core.exceptions import AuthenticationNotConfiguredError, PermissionDeniedError


class UserContext(Protocol):
    """Минимальный контракт пользователя для проверок доступа к endpoint-ам."""

    is_superuser: bool


async def get_current_user() -> UserContext:
    """Возвращает текущего пользователя после подключения слоя аутентификации."""
    raise AuthenticationNotConfiguredError()


async def get_current_superuser(
    current_user: Annotated[UserContext, Depends(get_current_user)],
) -> UserContext:
    """Проверяет, что текущий пользователь является superuser."""
    if not current_user.is_superuser:
        raise PermissionDeniedError()
    return current_user
