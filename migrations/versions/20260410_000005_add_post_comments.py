"""Добавляет таблицу комментариев к постам."""

import sqlalchemy as sa
from alembic import op

revision = "20260410_000005"
down_revision = "20260410_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Применяет миграцию комментариев к постам."""
    op.create_table(
        "post_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(length=1000), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_post_comments_author_id"), "post_comments", ["author_id"], unique=False)
    op.create_index(op.f("ix_post_comments_post_id"), "post_comments", ["post_id"], unique=False)


def downgrade() -> None:
    """Откатывает миграцию комментариев к постам."""
    op.drop_index(op.f("ix_post_comments_post_id"), table_name="post_comments")
    op.drop_index(op.f("ix_post_comments_author_id"), table_name="post_comments")
    op.drop_table("post_comments")
