"""Dependency-фабрики сервисов приложения."""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.crud.post_crud import PostCrud
from backend.app.crud.user_crud import UserCrud
from backend.app.db.session import get_db_session
from backend.app.services.auth_service import AuthService
from backend.app.services.media_service import MediaService
from backend.app.services.post_service import PostService


def get_auth_service(session: Session = Depends(get_db_session)) -> AuthService:
    """Возвращает сервис регистрации и авторизации."""
    settings = get_settings()
    return AuthService(user_crud=UserCrud(session=session), secret_key=settings.secret_key)


def get_post_service(session: Session = Depends(get_db_session)) -> PostService:
    """Возвращает сервис работы с постами."""
    return PostService(post_crud=PostCrud(session=session), user_crud=UserCrud(session=session))


def get_media_service() -> MediaService:
    """Возвращает сервис загрузки медиа в MinIO."""
    settings = get_settings()
    return MediaService(
        endpoint=settings.minio_endpoint,
        bucket_name=settings.minio_bucket_name,
        region=settings.minio_region,
        secure=settings.minio_secure,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        public_endpoint=settings.minio_public_endpoint,
    )
