"""Добавляет поля профиля пользователей и таблицу подписчиков."""

import sqlalchemy as sa
from alembic import op

revision = "20260410_000004"
down_revision = "20260410_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Применяет миграцию профиля пользователей."""
    op.add_column("users", sa.Column("avatar_url", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(length=1000), nullable=True))
    op.add_column(
        "users",
        sa.Column("level", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )

    op.create_table(
        "user_followers",
        sa.Column("follower_id", sa.Uuid(), nullable=False),
        sa.Column("followee_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["follower_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["followee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("follower_id", "followee_id"),
    )
    op.create_index(
        "ix_user_followers_follower_id",
        "user_followers",
        ["follower_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_followers_followee_id",
        "user_followers",
        ["followee_id"],
        unique=False,
    )


def downgrade() -> None:
    """Откатывает миграцию профиля пользователей."""
    op.drop_index("ix_user_followers_followee_id", table_name="user_followers")
    op.drop_index("ix_user_followers_follower_id", table_name="user_followers")
    op.drop_table("user_followers")

    op.drop_column("users", "level")
    op.drop_column("users", "bio")
    op.drop_column("users", "avatar_url")
