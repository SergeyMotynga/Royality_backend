import pytest
from backend.app.models.refresh_session import RefreshSession

pytestmark = pytest.mark.unit


def test_refresh_session_model_has_expected_table_and_fields() -> None:
    table = RefreshSession.__table__

    assert RefreshSession.__tablename__ == "refresh_sessions"
    assert "id" in table.columns
    assert "user_id" in table.columns
    assert "token_hash" in table.columns
    assert "expires_at" in table.columns
    assert "revoked_at" in table.columns
    assert "user_agent" in table.columns
    assert "ip_address" in table.columns
    assert "created_at" in table.columns

    assert table.c.user_id.nullable is False
    assert table.c.user_id.index is True
    assert table.c.token_hash.nullable is False
    assert table.c.token_hash.unique is True
    assert table.c.expires_at.nullable is False
    assert table.c.expires_at.index is True


def test_refresh_session_has_fk_to_users_with_cascade_delete() -> None:
    foreign_key = next(iter(RefreshSession.__table__.c.user_id.foreign_keys))

    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"


def test_refresh_session_relationship_to_user_is_selectin() -> None:
    relationship_property = RefreshSession.__mapper__.relationships["user"]

    assert relationship_property.lazy == "selectin"
    assert relationship_property.back_populates == "refresh_sessions"
