"""Зависимости API-слоя."""

from backend.app.api.deps.auth import get_auth_service
from backend.app.api.deps.common import get_current_superuser, get_current_user

__all__ = [
    "get_auth_service",
    "get_current_superuser",
    "get_current_user",
]
