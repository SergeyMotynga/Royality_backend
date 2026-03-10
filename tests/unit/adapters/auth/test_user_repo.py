from __future__ import annotations

import pytest
from backend.app.adapters.auth.user_repo import SqlAlchemyUserRepo
from backend.app.core.security import hash_password
from backend.app.models.user import User
from sqlalchemy import Select

pytestmark = pytest.mark.unit


class _FakeResult:
    def __init__(self, user: User | None) -> None:
        self.user = user

    def scalar_one_or_none(self) -> User | None:
        return self.user


class _FakeAsyncSession:
    def __init__(self, *, result_user: User | None = None) -> None:
        self.result_user = result_user
        self.execute_calls: list[object] = []
        self.added_entities: list[object] = []
        self.flush_called = False

    async def execute(self, statement: object) -> _FakeResult:
        self.execute_calls.append(statement)
        return _FakeResult(self.result_user)

    def add(self, entity: object) -> None:
        self.added_entities.append(entity)

    async def flush(self) -> None:
        self.flush_called = True


@pytest.mark.asyncio
async def test_get_by_email_returns_active_user() -> None:
    existing_user = User(
        email="user@example.com",
        password_hash=hash_password("sample_hash_value"),
    )
    session = _FakeAsyncSession(result_user=existing_user)
    repo = SqlAlchemyUserRepo(session=session)  # type: ignore[arg-type]

    found_user = await repo.get_by_email("user@example.com")

    assert found_user is existing_user
    assert len(session.execute_calls) == 1

    statement = session.execute_calls[0]
    assert isinstance(statement, Select)

    where_clause = str(statement.whereclause)
    assert "users.email" in where_clause
    assert "users.deleted_at IS NULL" in where_clause


@pytest.mark.asyncio
async def test_get_by_email_returns_none_when_user_not_found() -> None:
    session = _FakeAsyncSession(result_user=None)
    repo = SqlAlchemyUserRepo(session=session)  # type: ignore[arg-type]

    found_user = await repo.get_by_email("missing@example.com")

    assert found_user is None
    assert len(session.execute_calls) == 1


@pytest.mark.asyncio
async def test_create_user_adds_and_flushes_entity() -> None:
    session = _FakeAsyncSession()
    repo = SqlAlchemyUserRepo(session=session)  # type: ignore[arg-type]

    created_user = await repo.create_user(
        email="new@example.com",
        password_hash=hash_password("sample_hash_value"),
    )

    assert isinstance(created_user, User)
    assert created_user.email == "new@example.com"
    assert session.added_entities == [created_user]
    assert session.flush_called is True
