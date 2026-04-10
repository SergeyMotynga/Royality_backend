"""Пакет CRUD-компонентов доступа к данным."""

from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud

__all__ = ["PostCrud", "UserCrud"]
