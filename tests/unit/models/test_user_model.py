import pytest
from backend.app.models.user import User

pytestmark = pytest.mark.unit


def test_user_model_has_expected_table_and_fields() -> None:
    table = User.__table__

    assert User.__tablename__ == "users"
    assert "id" in table.columns
    assert "phone_number" in table.columns
    assert "email" in table.columns
    assert "password_hash" in table.columns
    assert "is_active" in table.columns
    assert "is_superuser" in table.columns
    assert "is_verified" in table.columns
    assert "created_at" in table.columns
    assert "updated_at" in table.columns
    assert "deleted_at" in table.columns

    assert table.c.phone_number.nullable is False
    assert table.c.phone_number.unique is True
    assert table.c.phone_number.index is True
    assert table.c.email.nullable is True
    assert table.c.password_hash.nullable is True
    assert table.c.is_active.default.arg is True
    assert table.c.is_superuser.default.arg is False
    assert table.c.is_verified.default.arg is False


def test_user_model_relationship_to_refresh_sessions_is_selectin() -> None:
    relationship_property = User.__mapper__.relationships["refresh_sessions"]

    assert relationship_property.lazy == "selectin"
    assert relationship_property.back_populates == "user"

