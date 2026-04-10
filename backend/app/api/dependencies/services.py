"""Dependency-фабрики сервисов приложения."""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.crud.user_crud import UserCrud
from backend.app.db.session import get_db_session
from backend.app.services.auth_service import AuthService


def get_auth_service(session: Session = Depends(get_db_session)) -> AuthService:
    """Возвращает сервис регистрации и авторизации."""
    settings = get_settings()
    return AuthService(user_crud=UserCrud(session=session), secret_key=settings.secret_key)
