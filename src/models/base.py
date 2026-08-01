from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def pk_uuid() -> str:
    return str(uuid4())


# ─── Centre ───────────────────────────────────────────────────────────────────


class Centre(Base):
    __tablename__ = "centres"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    district: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(100), index=True)
    capacity: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    staff: Mapped[list[Staff]] = relationship(back_populates="centre", cascade="all, delete-orphan")
    dogs: Mapped[list[Dog]] = relationship(back_populates="centre", cascade="all, delete-orphan")
    surgeries: Mapped[list[Surgery]] = relationship(back_populates="centre", cascade="all, delete-orphan")
    inspections: Mapped[list[Inspection]] = relationship(back_populates="centre", cascade="all, delete-orphan")
    allocations: Mapped[list[Allocation]] = relationship(back_populates="centre", cascade="all, delete-orphan")


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    centre_id: Mapped[str | None] = mapped_column(
        ForeignKey("centres.id"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))  # vet, surgeon, admin
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    centre: Mapped[Centre | None] = relationship(back_populates="staff")


class Dog(Base):
    __tablename__ = "dogs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id", ondelete="CASCADE"), index=True)
    tag_id: Mapped[str] = mapped_column(String(50), index=True)
    sex: Mapped[str] = mapped_column(String(10))
    age_estimate: Mapped[int | None] = mapped_column(default=None)
    weight: Mapped[float | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(String(20), default="registered")

    centre: Mapped[Centre] = relationship(back_populates="dogs")
    surgeries: Mapped[list[Surgery]] = relationship(
        back_populates="dog", cascade="all, delete-orphan"
    )


# ─── Surgery ──────────────────────────────────────────────────────────────────


class Surgery(Base):
    __tablename__ = "surgeries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    dog_id: Mapped[str] = mapped_column(ForeignKey("dogs.id"), index=True)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id", ondelete="CASCADE"), index=True)
    staff_id: Mapped[str] = mapped_column(ForeignKey("staff.id"), index=True)
    surgery_type: Mapped[str] = mapped_column(String(100))
    weight: Mapped[float | None] = mapped_column(default=None)
    complications: Mapped[str | None] = mapped_column(Text, default=None)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)
    synced_at: Mapped[datetime | None] = mapped_column(default=None)
    audit_hash: Mapped[str | None] = mapped_column(String(64), default=None)

    dog: Mapped[Dog] = relationship(back_populates="surgeries")
    centre: Mapped[Centre] = relationship(back_populates="surgeries")


# ─── Inspection ───────────────────────────────────────────────────────────────


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id", ondelete="CASCADE"), index=True)
    inspector_id: Mapped[str] = mapped_column(String(36))
    scheduled_at: Mapped[datetime | None] = mapped_column(default=None)
    conducted_at: Mapped[datetime | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    findings: Mapped[str | None] = mapped_column(Text, default=None)
    signoff_hash: Mapped[str | None] = mapped_column(String(64), default=None)

    centre: Mapped[Centre] = relationship(back_populates="inspections")


# ─── Fund Tracking ────────────────────────────────────────────────────────────


class Grant(Base):
    __tablename__ = "grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    awbi_ref: Mapped[str] = mapped_column(String(100), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    purpose: Mapped[str] = mapped_column(String(255))
    financial_year: Mapped[str] = mapped_column(String(9))
    status: Mapped[str] = mapped_column(String(20), default="active")

    allocations: Mapped[list[Allocation]] = relationship(back_populates="grant", cascade="all, delete-orphan")


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    grant_id: Mapped[str] = mapped_column(ForeignKey("grants.id"), index=True)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    allocated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    grant: Mapped[Grant] = relationship(back_populates="allocations")
    centre: Mapped[Centre] = relationship(back_populates="allocations")
    expenses: Mapped[list[Expense]] = relationship(back_populates="allocation", cascade="all, delete-orphan")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    allocation_id: Mapped[str] = mapped_column(ForeignKey("allocations.id", ondelete="CASCADE"), index=True)
    surgery_id: Mapped[str | None] = mapped_column(ForeignKey("surgeries.id"), default=None)
    category: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    bill_ref: Mapped[str | None] = mapped_column(String(100), default=None)
    expense_at: Mapped[date] = mapped_column(Date, default=date.today)

    allocation: Mapped[Allocation] = relationship(back_populates="expenses")


# ─── Audit ────────────────────────────────────────────────────────────────────


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[str] = mapped_column(String(36))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)


# ─── Complaint (Public) ───────────────────────────────────────────────────────


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id", ondelete="CASCADE"), index=True)
    citizen_phone: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")
    sla_deadline: Mapped[datetime | None] = mapped_column(default=None)
    resolution: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


# ─── Offline Sync Queue ───────────────────────────────────────────────────────


class SyncQueue(Base):
    __tablename__ = "sync_queue"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=pk_uuid)
    entity_type: Mapped[str] = mapped_column(
        String(50), index=True
    )  # surgery, dog, inspection, etc.
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    operation: Mapped[str] = mapped_column(String(20))  # create, update, delete
    payload: Mapped[dict] = mapped_column(JSON, default=dict)  # JSONB in PostgreSQL
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending, synced, failed
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    synced_at: Mapped[datetime | None] = mapped_column(default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
