"""Pydantic-схемы для постов."""

from datetime import datetime

from pydantic import BaseModel


class PostCreateRequest(BaseModel):
    """Тело запроса создания поста."""

    text: str
    medias: list[str]
    disable_comments: bool = False


class PostUpdateRequest(BaseModel):
    """Тело запроса редактирования поста."""

    text: str
    medias: list[str]
    disable_comments: bool = False


class PostAuthorResponse(BaseModel):
    """Информация об авторе поста."""

    id: str
    name: str
    avatar_url: str | None = None


class PostResponse(BaseModel):
    """Ответ с данными поста."""

    id: str
    text: str
    medias: list[str]
    disable_comments: bool
    author: PostAuthorResponse
    likes_count: int
    created_at: datetime
