"""Unit-тесты конфигурации приложения."""

import pytest

from backend.app.core.config import Settings, get_settings

BASE_ENV = {
    "ROYALITY_APP_TITLE": "Royality Backend Test",
    "ROYALITY_ENV": "test",
    "ROYALITY_LOG_LEVEL": "INFO",
    "ROYALITY_APP_HOST": "127.0.0.1",
    "ROYALITY_APP_PORT": "8000",
    "ROYALITY_POSTGRES_USER": "user",
    "ROYALITY_POSTGRES_PASSWORD": "password",
    "ROYALITY_POSTGRES_DB": "db",
    "ROYALITY_POSTGRES_HOST": "localhost",
    "ROYALITY_POSTGRES_PORT": "5432",
    "ROYALITY_MINIO_ROOT_USER": "minio-user",
    "ROYALITY_MINIO_ROOT_PASSWORD": "minio-password",
    "ROYALITY_MINIO_ENDPOINT": "localhost:9000",
    "ROYALITY_MINIO_BUCKET_NAME": "media",
    "ROYALITY_MINIO_REGION": "us-east-1",
    "ROYALITY_MINIO_SECURE": "false",
}


def _set_base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Заполняет обязательные переменные окружения базовыми значениями."""
    for key, value in BASE_ENV.items():
        monkeypatch.setenv(key, value)


@pytest.mark.unit
def test_resolved_database_url_uses_explicit_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет приоритет явного ROYALITY_DATABASE_URL."""
    _set_base_env(monkeypatch)
    monkeypatch.setenv("ROYALITY_DATABASE_URL", "postgresql+psycopg://explicit")

    settings = Settings(_env_file=None)

    assert settings.resolved_database_url == "postgresql+psycopg://explicit"


@pytest.mark.unit
def test_resolved_database_url_builds_from_parts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет сборку ROYALITY_DATABASE_URL из отдельных параметров."""
    _set_base_env(monkeypatch)
    monkeypatch.delenv("ROYALITY_DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.resolved_database_url == "postgresql+psycopg://user:password@localhost:5432/db"


@pytest.mark.unit
def test_get_settings_returns_cached_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет, что get_settings возвращает кэшированный объект."""
    _set_base_env(monkeypatch)
    monkeypatch.setenv("ROYALITY_DATABASE_URL", "postgresql+psycopg://cached")
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()
