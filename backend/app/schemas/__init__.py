"""Пакет Pydantic-схем."""

from backend.app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from backend.app.schemas.media import MediaUploadResponse
from backend.app.schemas.post import (
    PostAuthorResponse,
    PostCreateRequest,
    PostResponse,
    PostUpdateRequest,
)

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "MediaUploadResponse",
    "PostAuthorResponse",
    "PostCreateRequest",
    "PostResponse",
    "PostUpdateRequest",
    "SignupRequest",
    "SignupResponse",
]
