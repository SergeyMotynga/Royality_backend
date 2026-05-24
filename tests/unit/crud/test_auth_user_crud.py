from __future__ import annotations

import pytest
from backend.app.crud.auth import UserCrud
from backend.app.models.user import User
from sqlalchemy import Select

pytestmark = pytest.mark.unit


class _FakeResult:
    def __init__(self, value: object | None) -> None:
        self.value = value

    def scalar_one_or_none(self) -> object | None:
        return self.value


class _FakeAsyncSession:
    def __init__(self, *, execute_value: object | None = None) -> None:
        self.execute_value = execute_value
        self.execute_calls: list[object] = []
        self.added_entities: list[object] = []
        self.flush_called = False

    async def execute(self, statement: object) -> _FakeResult:
        self.execute_calls.append(statement)
        return _FakeResult(self.execute_value)

    def add(self, entity: object) -> None:
        self.added_entities.append(entity)

    async def flush(self) -> None:
        self.flush_called = True


@pytest.mark.asyncio
async def test_get_by_phone_number_returns_active_user() -> None:
    existing_user = User(phone_number="+79991234567")
    session = _FakeAsyncSession(execute_value=existing_user)
    crud = UserCrud(session=session)  # type: ignore[arg-type]

    found_user = await crud.get_by_phone_number("+79991234567")

    assert found_user is existing_user
    assert len(session.execute_calls) == 1

    statement = session.execute_calls[0]
    assert isinstance(statement, Select)

    where_clause = str(statement.whereclause)
    assert "users.phone_number" in where_clause
    assert "users.deleted_at IS NULL" in where_clause


@pytest.mark.asyncio
async def test_get_by_phone_number_returns_none_when_user_not_found() -> None:
    session = _FakeAsyncSession(execute_value=None)
    crud = UserCrud(session=session)  # type: ignore[arg-type]

    found_user = await crud.get_by_phone_number("+79990000000")

    assert found_user is None
    assert len(session.execute_calls) == 1


@pytest.mark.asyncio
async def test_create_user_adds_and_flushes_entity() -> None:
    session = _FakeAsyncSession()
    crud = UserCrud(session=session)  # type: ignore[arg-type]

    created_user = await crud.create_user(phone_number="+79991234567", is_verified=True)

    assert isinstance(created_user, User)
    assert created_user.phone_number == "+79991234567"
    assert created_user.is_verified is True
    assert session.added_entities == [created_user]
    assert session.flush_called is True


@pytest.mark.asyncio
async def test_mark_user_verified_sets_flag_and_flushes() -> None:
    session = _FakeAsyncSession()
    crud = UserCrud(session=session)  # type: ignore[arg-type]
    user = User(phone_number="+79991234567", is_verified=False)

    result = await crud.mark_user_verified(user=user)

    assert result is user
    assert user.is_verified is True
    assert session.flush_called is True
