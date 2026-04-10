"""Добавляет таблицу пользователей."""

import sqlalchemy as sa
from alembic import op

revision = "20260410_000002"
down_revision = "20260409_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Применяет миграцию добавления пользователей."""
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("login", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_login"), "users", ["login"], unique=True)


def downgrade() -> None:
    """Откатывает миграцию добавления пользователей."""
    op.drop_index(op.f("ix_users_login"), table_name="users")
    op.drop_table("users")
