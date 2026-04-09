"""Unit-тесты базового ORM-класса."""

import pytest
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class OrmEntity(Base):
    """Тестовая ORM-сущность."""

    __tablename__ = "test_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


@pytest.mark.unit
def test_base_metadata_contains_declared_table() -> None:
    """Проверяет регистрацию таблицы в metadata."""
    assert "test_entities" in Base.metadata.tables
