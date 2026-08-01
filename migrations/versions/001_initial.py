"""Initial migration: create all domain tables.

Revision ID: 001
Revises:
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# FK target constant to avoid duplication
CENTRES_FK = "centres.id"


def upgrade() -> None:
    op.create_table(
        "centres",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("district", sa.String(255), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("capacity", sa.Integer, server_default="0", nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_centres_code", "centres", ["code"], unique=True)
    op.create_index("ix_centres_state", "centres", ["state"])

    op.create_table(
        "staff",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("centre_id", sa.String(36), sa.ForeignKey(CENTRES_FK), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("active", sa.Boolean, server_default="true", nullable=False),
    )
    op.create_index("ix_staff_centre_id", "staff", ["centre_id"])

    op.create_table(
        "dogs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("centre_id", sa.String(36), sa.ForeignKey(CENTRES_FK), nullable=False),
        sa.Column("tag_id", sa.String(50), nullable=False),
        sa.Column("sex", sa.String(10), nullable=False),
        sa.Column("age_estimate", sa.Integer, nullable=True),
        sa.Column("weight", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), server_default="registered", nullable=False),
    )
    op.create_index("ix_dogs_centre_id", "dogs", ["centre_id"])
    op.create_index("ix_dogs_tag_id", "dogs", ["tag_id"])

    op.create_table(
        "surgeries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dog_id", sa.String(36), sa.ForeignKey("dogs.id"), nullable=False),
        sa.Column("centre_id", sa.String(36), sa.ForeignKey(CENTRES_FK), nullable=False),
        sa.Column("staff_id", sa.String(36), sa.ForeignKey("staff.id"), nullable=False),
        sa.Column("surgery_type", sa.String(100), nullable=False),
        sa.Column("weight", sa.Float, nullable=True),
        sa.Column("complications", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("synced_at", sa.DateTime, nullable=True),
        sa.Column("audit_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_surgeries_dog_id", "surgeries", ["dog_id"])
    op.create_index("ix_surgeries_centre_id", "surgeries", ["centre_id"])
    op.create_index("ix_surgeries_timestamp", "surgeries", ["timestamp"])

    op.create_table(
        "inspections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("centre_id", sa.String(36), sa.ForeignKey(CENTRES_FK), nullable=False),
        sa.Column("inspector_id", sa.String(36), nullable=False),
        sa.Column("scheduled_at", sa.DateTime, nullable=True),
        sa.Column("conducted_at", sa.DateTime, nullable=True),
        sa.Column("status", sa.String(20), server_default="scheduled", nullable=False),
        sa.Column("findings", sa.Text, nullable=True),
        sa.Column("signoff_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_inspections_centre_id", "inspections", ["centre_id"])

    op.create_table(
        "grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("awbi_ref", sa.String(100), nullable=False, unique=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("purpose", sa.String(255), nullable=False),
        sa.Column("financial_year", sa.String(9), nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
    )

    op.create_table(
        "allocations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("grant_id", sa.String(36), sa.ForeignKey("grants.id"), nullable=False),
        sa.Column("centre_id", sa.String(36), sa.ForeignKey(CENTRES_FK), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("allocated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_allocations_grant_id", "allocations", ["grant_id"])
    op.create_index("ix_allocations_centre_id", "allocations", ["centre_id"])

    op.create_table(
        "expenses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("allocation_id", sa.String(36), sa.ForeignKey("allocations.id"), nullable=False),
        sa.Column("surgery_id", sa.String(36), sa.ForeignKey("surgeries.id"), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("bill_ref", sa.String(100), nullable=True),
        sa.Column("expense_at", sa.Date, server_default=sa.func.current_date(), nullable=False),
    )
    op.create_index("ix_expenses_allocation_id", "expenses", ["allocation_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])

    op.create_table(
        "complaints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("centre_id", sa.String(36), sa.ForeignKey(CENTRES_FK), nullable=False),
        sa.Column("citizen_phone", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), server_default="open", nullable=False),
        sa.Column("sla_deadline", sa.DateTime, nullable=True),
        sa.Column("resolution", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_complaints_centre_id", "complaints", ["centre_id"])


def downgrade() -> None:
    op.drop_table("expenses")
    op.drop_table("allocations")
    op.drop_table("grants")
    op.drop_table("inspections")
    op.drop_table("surgeries")
    op.drop_table("dogs")
    op.drop_table("staff")
    op.drop_table("complaints")
    op.drop_table("audit_events")
    op.drop_table("centres")