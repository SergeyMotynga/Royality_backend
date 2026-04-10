"""Unit-тесты CRUD-слоя пользователей."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.crud.user_crud import UserCrud
from backend.app.db.base import Base


@pytest.fixture
def db_session() -> Session:
    """Создает изолированную SQLite-сессию для CRUD-тестов."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    local_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = local_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.unit
def test_get_by_login_returns_none(db_session: Session) -> None:
    """Проверяет отсутствие пользователя по логину."""
    crud = UserCrud(session=db_session)

    result = crud.get_by_login(login="missing")

    assert result is None


@pytest.mark.unit
def test_create_user_and_get_by_login(db_session: Session) -> None:
    """Проверяет создание пользователя и последующий поиск по логину."""
    crud = UserCrud(session=db_session)

    created = crud.create_user(login="test-user", password_hash="hash", name="Тестовый")
    found = crud.get_by_login(login="test-user")

    assert str(created.id) == str(found.id)
    assert found.login == "test-user"
    assert found.name == "Тестовый"


@pytest.mark.unit
def test_get_by_id_returns_user(db_session: Session) -> None:
    """Проверяет поиск пользователя по идентификатору."""
    crud = UserCrud(session=db_session)
    created = crud.create_user(login="by-id-user", password_hash="hash", name="По ID")

    found = crud.get_by_id(user_id=created.id)

    assert found is not None
    assert str(found.id) == str(created.id)
    assert found.login == "by-id-user"
