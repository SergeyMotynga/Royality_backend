import pytest
from backend.app.models import RefreshSession, User
from sqlalchemy import DateTime

pytestmark = pytest.mark.unit


def test_uuid_primary_key_mixin_applies_uuid_pk_field() -> None:
    assert User.__table__.c.id.primary_key is True
    assert RefreshSession.__table__.c.id.primary_key is True


def test_created_at_mixin_uses_timezone_and_server_default() -> None:
    created_at_type = User.__table__.c.created_at.type

    assert isinstance(created_at_type, DateTime)
    assert created_at_type.timezone is True
    assert User.__table__.c.created_at.server_default is not None
    assert RefreshSession.__table__.c.created_at.server_default is not None


def test_timestamp_mixin_uses_timezone_and_server_default_for_updated_at() -> None:
    updated_at_column = User.__table__.c.updated_at
    updated_at_type = updated_at_column.type

    assert isinstance(updated_at_type, DateTime)
    assert updated_at_type.timezone is True
    assert updated_at_column.server_default is not None


def test_soft_delete_mixin_adds_nullable_deleted_at() -> None:
    deleted_at_column = User.__table__.c.deleted_at
    deleted_at_type = deleted_at_column.type

    assert isinstance(deleted_at_type, DateTime)
    assert deleted_at_type.timezone is True
    assert deleted_at_column.nullable is True
