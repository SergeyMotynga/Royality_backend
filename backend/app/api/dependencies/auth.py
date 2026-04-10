"""Зависимости авторизации и ролевого доступа."""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from jwt import InvalidTokenError

from backend.app.core.config import get_settings
from backend.app.core.security import decode_access_token


@dataclass(frozen=True)
class CurrentUser:
    """Текущая авторизованная сущность пользователя."""

    user_id: str
    is_superuser: bool


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> CurrentUser:
    """Возвращает текущего пользователя из заголовков запроса."""
    if authorization:
        token_type, _, token = authorization.partition(" ")
        if token_type.lower() != "bearer" or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Некорректный формат заголовка Authorization",
            )
        settings = get_settings()
        try:
            payload = decode_access_token(token=token, secret_key=settings.secret_key)
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Некорректный access token",
            ) from exc
        user_id = str(payload.get("sub", "")).strip()
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен не содержит идентификатор пользователя",
            )
        return CurrentUser(
            user_id=user_id,
            is_superuser=bool(payload.get("is_superuser", False)),
        )

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
