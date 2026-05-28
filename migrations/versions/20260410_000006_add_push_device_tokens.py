"""Добавляет таблицу FCM-токенов устройств пользователей.

Revision ID: 20260410_000006
Revises: 20260410_000005
Create Date: 2026-04-10 00:00:06.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260410_000006"
down_revision: str | None = "20260410_000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создает таблицу FCM-токенов устройств."""
    op.create_table(
        "push_device_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=4096), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("device_id", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_push_device_tokens_token", "push_device_tokens", ["token"], unique=True)
    op.create_index("ix_push_device_tokens_user_id", "push_device_tokens", ["user_id"])


def downgrade() -> None:
    """Удаляет таблицу FCM-токенов устройств."""
    op.drop_index("ix_push_device_tokens_user_id", table_name="push_device_tokens")
    op.drop_index("ix_push_device_tokens_token", table_name="push_device_tokens")
    op.drop_table("push_device_tokens")
