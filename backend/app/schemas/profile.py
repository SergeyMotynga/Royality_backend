"""Pydantic-схемы профиля пользователя."""

from datetime import datetime

from pydantic import BaseModel


class UserProfileUpdateRequest(BaseModel):
    """Тело запроса обновления профиля текущего пользователя."""

    nickname: str
    avatar_url: str | None = None
    bio: str | None = None
    level: int


class UserProfileResponse(BaseModel):
    """Ответ с данными профиля пользователя."""

    id: str
    nickname: str
    avatar_url: str | None
    bio: str | None
    level: int
    posts_count: int
    followers_count: int
    is_following: bool
    created_at: datetime
