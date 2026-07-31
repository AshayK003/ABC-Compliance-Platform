"""Add sync_queue table and make staff.centre_id nullable.

Revision ID: 002
Revises: 001
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: str = "001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Add sync_queue table
    op.create_table(
        "sync_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False, index=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("payload", sa.Text, server_default="{}", nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False, index=True),
        sa.Column("retry_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("synced_at", sa.DateTime, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
    )

    # Make staff.centre_id nullable (was NOT NULL in 001, but model is nullable=True)
    op.alter_column("staff", "centre_id", existing_type=sa.String(36), nullable=True)


def downgrade() -> None:
    op.drop_table("sync_queue")

    # Revert staff.centre_id to NOT NULL
    op.alter_column("staff", "centre_id", existing_type=sa.String(36), nullable=False)