"""Add token_version to staff for refresh token revocation.

Revision ID: 003
Revises: 002
Create Date: 2026-08-15
"""

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str = "002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Add token_version column to staff with default 0
    op.add_column(
        "staff",
        sa.Column("token_version", sa.Integer, server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("staff", "token_version")
