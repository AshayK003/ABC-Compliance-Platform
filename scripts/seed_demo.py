"""Seed the database with realistic demo data for the ABC Compliance Platform.

Idempotent: clears demo-scoped tables (dogs, surgeries, inspections, grants,
allocations, expenses) then inserts a fresh set of records tied to the
existing centres and staff. Centres/staff themselves are never touched.

Usage:
    env -u PYTHONPATH ./.venv/Scripts/python.exe scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select

from src.database import async_session
from src.models.base import (
    Allocation,
    Centre,
    Dog,
    Expense,
    Grant,
    Inspection,
    Staff,
    Surgery,
)

# Existing records (looked up by code/phone — do not hardcode UUIDs)
CENTRE_CODES = {"BBMP001", "BBMP002", "TC01"}


async def seed() -> None:
    async with async_session() as db:
        centres = {c.code: c for c in (await db.execute(select(Centre))).scalars()}
        staff = {s.phone: s for s in (await db.execute(select(Staff))).scalars()}

        # Clear demo-scoped tables
        for model in (Expense, Allocation, Grant, Inspection, Surgery, Dog):
            await db.execute(delete(model))
        await db.commit()

        c1, c2, c3 = centres["BBMP001"], centres["BBMP002"], centres["TC01"]
        vet = staff["9888888888"]  # Test Vet
        admin = staff["9999999999"]  # Test Admin 2

        # ─── Dogs ────────────────────────────────────────────────────────────
        dogs = [
            Dog(centre_id=c1.id, tag_id="BLR-0001", sex="F", age_estimate=2, weight=14.5, status="registered"),
            Dog(centre_id=c1.id, tag_id="BLR-0002", sex="M", age_estimate=3, weight=18.0, status="registered"),
            Dog(centre_id=c2.id, tag_id="BLR-0101", sex="F", age_estimate=1, weight=9.5, status="registered"),
            Dog(centre_id=c3.id, tag_id="TC-0001", sex="M", age_estimate=4, weight=22.0, status="registered"),
        ]
        db.add_all(dogs)
        await db.commit()
        for d in dogs:
            await db.refresh(d)

        # ─── Surgeries ───────────────────────────────────────────────────────
        now = datetime.utcnow().replace(tzinfo=None)
        surgeries = [
            Surgery(
                dog_id=dogs[0].id, centre_id=c1.id, staff_id=vet.id,
                surgery_type="Spay (OVH)", weight=14.5, complications=None,
                timestamp=now - timedelta(hours=1),
            ),
            Surgery(
                dog_id=dogs[1].id, centre_id=c1.id, staff_id=vet.id,
                surgery_type="Neuter (Castration)", weight=18.0, complications=None,
                timestamp=now - timedelta(hours=9),
            ),
            Surgery(
                dog_id=dogs[2].id, centre_id=c2.id, staff_id=vet.id,
                surgery_type="Spay (OVH)", weight=9.5, complications="Mild post-op swelling, resolved",
                timestamp=now - timedelta(days=4),
            ),
            Surgery(
                dog_id=dogs[3].id, centre_id=c3.id, staff_id=vet.id,
                surgery_type="Tumor removal", weight=22.0, complications=None,
                timestamp=now - timedelta(days=12),
            ),
        ]
        db.add_all(surgeries)
        await db.commit()
        for s in surgeries:
            await db.refresh(s)

        # ─── Inspections ─────────────────────────────────────────────────────
        inspections = [
            Inspection(
                centre_id=c1.id, inspector_id=admin.id, status="completed",
                scheduled_at=now - timedelta(days=10), conducted_at=now - timedelta(days=9),
                findings="All records in order. Surgical log complete, no discrepancies.",
            ),
            Inspection(
                centre_id=c2.id, inspector_id=admin.id, status="scheduled",
                scheduled_at=now + timedelta(days=4), conducted_at=None, findings=None,
            ),
        ]
        db.add_all(inspections)

        # ─── Grants & allocations ────────────────────────────────────────────
        grant1 = Grant(
            awbi_ref="AWBI/2026/GR/0042", amount=Decimal("250000.00"),
            purpose="Sterilization programme Q2", financial_year="2026-27", status="active",
        )
        grant2 = Grant(
            awbi_ref="AWBI/2026/GR/0051", amount=Decimal("120000.00"),
            purpose="Infrastructure upgrade", financial_year="2026-27", status="active",
        )
        db.add_all([grant1, grant2])
        await db.commit()
        await db.refresh(grant1)
        await db.refresh(grant2)

        alloc1 = Allocation(grant_id=grant1.id, centre_id=c1.id, amount=Decimal("150000.00"), allocated_at=now - timedelta(days=25))
        alloc2 = Allocation(grant_id=grant1.id, centre_id=c2.id, amount=Decimal("100000.00"), allocated_at=now - timedelta(days=25))
        alloc3 = Allocation(grant_id=grant2.id, centre_id=c1.id, amount=Decimal("120000.00"), allocated_at=now - timedelta(days=5))
        db.add_all([alloc1, alloc2, alloc3])
        await db.commit()
        for a in (alloc1, alloc2, alloc3):
            await db.refresh(a)

        # ─── Expenses ────────────────────────────────────────────────────────
        expenses = [
            Expense(
                allocation_id=alloc1.id, surgery_id=surgeries[0].id, category="Consumables",
                amount=Decimal("4500.00"), bill_ref="BILL/2026/0718", expense_at=date.today() - timedelta(days=16),
            ),
            Expense(
                allocation_id=alloc1.id, surgery_id=surgeries[1].id, category="Vaccines",
                amount=Decimal("2800.00"), bill_ref="BILL/2026/0724", expense_at=date.today() - timedelta(days=10),
            ),
            Expense(
                allocation_id=alloc2.id, surgery_id=surgeries[2].id, category="Medication",
                amount=Decimal("3900.00"), bill_ref="BILL/2026/0728", expense_at=date.today() - timedelta(days=5),
            ),
            Expense(
                allocation_id=alloc3.id, surgery_id=surgeries[3].id, category="Equipment",
                amount=Decimal("15000.00"), bill_ref="BILL/2026/0730", expense_at=date.today() - timedelta(days=2),
            ),
        ]
        db.add_all(expenses)
        await db.commit()

    print("Seeded: 4 dogs, 4 surgeries, 2 inspections, 2 grants, 3 allocations, 4 expenses")


if __name__ == "__main__":
    asyncio.run(seed())
