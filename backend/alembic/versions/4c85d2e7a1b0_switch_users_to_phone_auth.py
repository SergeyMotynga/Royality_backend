"""Switch users auth fields to phone-based flow.

Revision ID: 4c85d2e7a1b0
Revises: 2d6f177657c4
Create Date: 2026-03-30 02:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c85d2e7a1b0"
down_revision: Union[str, Sequence[str], None] = "2d6f177657c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration."""
    op.add_column("users", sa.Column("phone_number", sa.String(length=32), nullable=True))
    op.create_index(op.f("ix_users_phone_number"), "users", ["phone_number"], unique=True)
    op.execute("UPDATE users SET phone_number = REPLACE(id::text, '-', '') WHERE phone_number IS NULL")
    op.alter_column("users", "phone_number", existing_type=sa.String(length=32), nullable=False)

    op.alter_column("users", "email", existing_type=sa.String(length=320), nullable=True)
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    """Rollback migration."""
    op.alter_column("users", "phone_number", existing_type=sa.String(length=32), nullable=True)
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("users", "email", existing_type=sa.String(length=320), nullable=False)

    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_column("users", "phone_number")
