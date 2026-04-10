"""Зависимости авторизации и ролевого доступа."""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from backend.app.core.config import get_settings
from backend.app.core.security import decode_access_token


@dataclass(frozen=True)
class CurrentUser:
    """Текущая авторизованная сущность пользователя."""

    user_id: str
    is_superuser: bool


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> CurrentUser:
    """Возвращает текущего пользователя из заголовков запроса."""
    if credentials is not None:
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Некорректный формат заголовка Authorization",
            )
        token = credentials.credentials
        if not token:
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

    if x_user_id:
        return CurrentUser(
            user_id=x_user_id,
            is_superuser=(x_role or "").lower() == "admin",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Требуется авторизация",
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
