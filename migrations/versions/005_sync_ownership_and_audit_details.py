"""Sync ownership + audit details.

Revision ID: 005
Revises: 004
Create Date: 2026-09-03
"""

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str = "004"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Who enqueued the item: NULL = legacy pre-ownership row (grandfathered:
    # any authenticated user may still transition it).
    op.add_column(
        "sync_queue",
        sa.Column("owner_id", sa.String(36), nullable=True, index=True),
    )
    op.create_foreign_key(
        "fk_sync_queue_owner",
        "sync_queue",
        "staff",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Audit event payload (log_audit_event accepted `details` but dropped it).
    op.add_column("audit_events", sa.Column("details", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_constraint("fk_sync_queue_owner", "sync_queue", type_="foreignkey")
    op.drop_column("sync_queue", "owner_id")
    op.drop_column("audit_events", "details")
