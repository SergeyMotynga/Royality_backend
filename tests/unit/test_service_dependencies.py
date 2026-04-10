"""Unit-тесты dependency-фабрик сервисов."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.dependencies.services import (
    get_auth_service,
    get_media_service,
    get_post_service,
)
from backend.app.db.session import get_db_session
from backend.app.services.auth_service import AuthService
from backend.app.services.media_service import MediaService
from backend.app.services.post_service import PostService


@pytest.mark.unit
def test_get_db_session_returns_session_object() -> None:
    """Проверяет, что dependency БД возвращает объект сессии."""
    generator = get_db_session()
    session = next(generator)

    assert session.is_active is True

    generator.close()


@pytest.mark.unit
def test_get_auth_service_returns_auth_service() -> None:
    """Проверяет создание AuthService из dependency-фабрики."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    service = get_auth_service(session=session)

    assert isinstance(service, AuthService)

    session.close()


@pytest.mark.unit
def test_get_post_service_returns_post_service() -> None:
    """Проверяет создание PostService из dependency-фабрики."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    service = get_post_service(session=session)

    assert isinstance(service, PostService)

    session.close()


@pytest.mark.unit
def test_get_media_service_returns_media_service() -> None:
    """Проверяет создание MediaService из dependency-фабрики."""
    service = get_media_service()

    assert isinstance(service, MediaService)
