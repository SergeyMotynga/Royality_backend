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


class PostCommentCreateRequest(BaseModel):
    """Тело запроса создания комментария."""

    text: str


class PostCommentUpdateRequest(BaseModel):
    """Тело запроса редактирования комментария."""

    text: str


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
    comments_count: int
    is_liked: bool
    created_at: datetime


class PostCommentResponse(BaseModel):
    """Ответ с данными комментария к посту."""

    id: str
    post_id: str
    text: str
    author: PostAuthorResponse
    created_at: datetime
    updated_at: datetime
