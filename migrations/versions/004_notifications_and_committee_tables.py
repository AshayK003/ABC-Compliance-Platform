"""Create notifications and committee tables missing from earlier migrations.

Revision ID: 004
Revises: 003
Create Date: 2026-08-22
"""

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str = "003"
branch_labels: str | None = None
depends_on: str | None = None

_COMMITTEES_FK = "committees.id"


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False, server_default="info"),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )
    op.create_table(
        "committees",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "meetings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("committee_id", sa.String(36),
                  sa.ForeignKey(_COMMITTEES_FK, ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("meeting_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("meeting_id", sa.String(36),
                  sa.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("resolution_id", sa.String(100), nullable=False, unique=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "votes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("decision_id", sa.String(36),
                  sa.ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("member_id", sa.String(36), nullable=False, index=True),
        sa.Column("vote", sa.String(20), nullable=False),
        sa.Column("voted_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "committee_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("committee_id", sa.String(36),
                  sa.ForeignKey(_COMMITTEES_FK, ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("member_id", sa.String(36),
                  sa.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "meeting_attendees",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("meeting_id", sa.String(36),
                  sa.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("staff_id", sa.String(36),
                  sa.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("attended", sa.Boolean(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
    )
    op.create_table(
        "committee_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("committee_id", sa.String(36),
                  sa.ForeignKey(_COMMITTEES_FK, ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.String(36), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("committee_documents")
    op.drop_table("meeting_attendees")
    op.drop_table("committee_members")
    op.drop_table("votes")
    op.drop_table("decisions")
    op.drop_table("meetings")
    op.drop_table("committees")
    op.drop_table("notifications")
