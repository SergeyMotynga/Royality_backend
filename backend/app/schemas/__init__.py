"""Пакет Pydantic-схем."""

from backend.app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from backend.app.schemas.media import MediaUploadResponse
from backend.app.schemas.post import (
    PostAuthorResponse,
    PostCreateRequest,
    PostResponse,
    PostUpdateRequest,
)
from backend.app.schemas.profile import UserProfileResponse, UserProfileUpdateRequest

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "MediaUploadResponse",
    "PostAuthorResponse",
    "PostCreateRequest",
    "PostResponse",
    "PostUpdateRequest",
    "UserProfileResponse",
    "UserProfileUpdateRequest",
    "SignupRequest",
    "SignupResponse",
]
