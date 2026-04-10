"""Pydantic-схемы для загрузки медиа."""

from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    """Ответ успешной загрузки медиа."""

    url: str
