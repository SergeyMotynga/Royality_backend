"""Вспомогательные функции конфигурации Alembic."""

from __future__ import annotations

from importlib import import_module

from sqlalchemy import MetaData

from backend.app.core.config import get_settings
from backend.app.db.base import Base


def get_target_metadata() -> MetaData:
    """Возвращает metadata ORM-моделей для autogenerate."""
    import_module("backend.app.models")
    return Base.metadata


def get_alembic_database_url() -> str:
    """Возвращает URL базы данных для запуска миграций."""
    return get_settings().database_url
