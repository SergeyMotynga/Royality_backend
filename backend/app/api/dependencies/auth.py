"""Зависимости авторизации и ролевого доступа."""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status


@dataclass(frozen=True)
class CurrentUser:
    """Текущая авторизованная сущность пользователя."""

    user_id: str
    is_superuser: bool


async def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> CurrentUser:
    """Возвращает текущего пользователя из заголовков запроса."""
    return CurrentUser(
        user_id=x_user_id or "local-user",
        is_superuser=(x_role or "").lower() == "admin",
    )


async def get_current_superuser(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Проверяет, что текущий пользователь имеет права администратора."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа",
        )
    return current_user
