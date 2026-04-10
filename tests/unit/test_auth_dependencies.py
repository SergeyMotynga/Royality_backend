"""Unit-тесты зависимостей авторизации."""

import pytest
from fastapi import HTTPException

from backend.app.api.dependencies.auth import CurrentUser, get_current_superuser, get_current_user
from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_uses_default_values() -> None:
    """Проверяет значения пользователя по умолчанию."""
    user = await get_current_user(authorization=None, x_user_id=None, x_role=None)

    assert user == CurrentUser(user_id="local-user", is_superuser=False)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_for_admin_role() -> None:
    """Проверяет распознавание роли администратора."""
    user = await get_current_user(authorization=None, x_user_id="user-1", x_role="admin")

    assert user == CurrentUser(user_id="user-1", is_superuser=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_from_bearer_token() -> None:
    """Проверяет извлечение пользователя из bearer-токена."""
    token = create_access_token(
        secret_key=get_settings().secret_key,
        user_id="token-user",
        login="token-login",
        is_superuser=True,
    )

    user = await get_current_user(authorization=f"Bearer {token}")

    assert user == CurrentUser(user_id="token-user", is_superuser=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_invalid_authorization_format() -> None:
    """Проверяет ошибку некорректного формата Authorization."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Token abc")

    assert exc_info.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_invalid_token() -> None:
    """Проверяет ошибку некорректного access token."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer invalid-token")

    assert exc_info.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_superuser_raises_for_non_admin() -> None:
    """Проверяет ошибку при попытке доступа без роли администратора."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_superuser(CurrentUser(user_id="user-1", is_superuser=False))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Недостаточно прав доступа"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_superuser_returns_user() -> None:
    """Проверяет успешный доступ администратора."""
    current_user = CurrentUser(user_id="admin-1", is_superuser=True)

    result = await get_current_superuser(current_user)

    assert result == current_user
