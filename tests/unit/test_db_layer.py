import pytest
from backend.app.db.base import NAMING_CONVENTION, Base, metadata
from backend.app.db.session import AsyncSessionLocal, get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


def test_naming_convention_contains_expected_keys() -> None:
    assert NAMING_CONVENTION["ix"] == "ix_%(table_name)s_%(column_0_name)s"
    assert NAMING_CONVENTION["uq"] == "uq_%(table_name)s_%(column_0_name)s"
    assert NAMING_CONVENTION["ck"] == "ck_%(table_name)s_%(constraint_name)s"
    assert NAMING_CONVENTION["fk"] == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    assert NAMING_CONVENTION["pk"] == "pk_%(table_name)s"


def test_base_uses_shared_metadata() -> None:
    assert Base.metadata is metadata


def test_async_session_factory_has_expected_options() -> None:
    assert AsyncSessionLocal.kw["autocommit"] is False
    assert AsyncSessionLocal.kw["autoflush"] is False
    assert AsyncSessionLocal.kw["expire_on_commit"] is False
    assert AsyncSessionLocal.class_ is AsyncSession


@pytest.mark.asyncio
async def test_get_db_session_returns_async_session() -> None:
    generator = get_db_session()

    try:
        session = await anext(generator)
        assert isinstance(session, AsyncSession)
    finally:
        await generator.aclose()
