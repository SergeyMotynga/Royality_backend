import pytest
from backend.app.core.config import get_settings
from backend.app.db.alembic_config import get_alembic_database_url, get_target_metadata

pytestmark = pytest.mark.unit


def test_get_target_metadata_contains_auth_tables() -> None:
    metadata = get_target_metadata()

    assert "users" in metadata.tables
    assert "refresh_sessions" in metadata.tables


def test_get_alembic_database_url_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_url = "postgresql+psycopg://test:test@localhost:5432/test_db"
    monkeypatch.setenv("DATABASE_URL", expected_url)
    get_settings.cache_clear()

    database_url = get_alembic_database_url()

    assert database_url == expected_url
    get_settings.cache_clear()
