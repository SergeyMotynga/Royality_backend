"""Пакет зависимостей API."""

from backend.app.api.dependencies.auth import CurrentUser, get_current_superuser, get_current_user
from backend.app.api.dependencies.services import get_auth_service, get_post_service

__all__ = [
    "CurrentUser",
    "get_auth_service",
    "get_current_superuser",
    "get_current_user",
    "get_post_service",
]
