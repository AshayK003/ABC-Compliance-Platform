"""Seed the database with realistic demo data for the ABC Compliance Platform.

Data-driven: uses whatever centres exist in the DB (run scripts/seed_awbi_centres.py
first for the official AWBI-recognised centre list) and generates realistic
operational data at demo scale:

  - 10 grants with AWBI-style references (₹5L-₹50L, 2024-25 to 2026-27)
  - ~15 allocations across active grants and a subset of centres
  - ~90 expenses tied to those allocations (bills, consumables, equipment)
  - ~180 dogs across centres, each with 1-2 surgeries in the last 6 months
  - ~80 inspections on a quarterly cycle (completed/scheduled/overdue)

Idempotent: clears demo-scoped tables (dogs, surgeries, inspections, grants,
allocations, expenses) then inserts a fresh set. Centres and existing staff
are never touched. Creates a demo vet and surgeon if they don't already exist.

Usage (from project root):
  DATABASE_URL="postgresql+asyncpg://abc:abc@localhost:5433/abc_dashboard" \\
    env -u PYTHONPATH ./.venv/Scripts/python.exe scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
import os
import random
import secrets
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select

from src.database import async_session
from src.models.base import (
    Allocation,
    Centre,
    Committee,
    CommitteeDocument,
    CommitteeMember,
    Decision,
    Dog,
    Expense,
    Grant,
    Inspection,
    Meeting,
    Staff,
    Surgery,
    Vote,
)

random.seed(42)  # deterministic demo data

SURGERY_TYPES = ["Spay (OVH)", "Neuter (Castration)", "Tumor removal", "Wound repair", "Vaccination boost", "Dental cleaning"]
COMPLICATIONS_POOL = [None, None, None, None, "Mild post-op swelling, resolved", "Minor wound infection, treated", None, None]
EXPENSE_CATEGORIES = ["Consumables", "Vaccines", "Medication", "Equipment", "Anesthesia supplies", "Infrastructure", "Staff training"]
PURPOSES = [
    "Sterilization programme", "Infrastructure upgrade", "Anti-rabies vaccination drive",
    "Emergency medical equipment", "Feeding programme support", "Staff training & capacity building",
]
FINDINGS_POOL = [
    "All records in order. Surgical log complete, no discrepancies.",
    "Minor record-keeping gaps found; corrective action advised within 30 days.",
    "Satisfactory compliance. Sterilization targets met for the quarter.",
    "Post-operative care logs incomplete for 2 cases; follow-up inspection scheduled.",
    "No issues found. Centre operating within ABC Rules 2023 requirements.",
]

DEMO_VET_PHONE = "9888888888"
DEMO_SURGEON_PHONE = "9777777777"


def state_financial_year() -> str:
    """Return the current AWBI financial year, e.g. 2026-27."""
    today = date.today()
    start = today.year if today.month >= 4 else today.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


async def seed() -> None:
    async with async_session() as db:
        centres = list((await db.execute(select(Centre).order_by(Centre.name))).scalars())
        if not centres:
            print("No centres found. Run scripts/seed_awbi_centres.py first.")
            return

        staff = list((await db.execute(select(Staff))).scalars())

        # Ensure demo vet + surgeon exist. Demo passwords are random per-seed
        # (or from DEMO_PASSWORD env) — never static literals.
        demo_password = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(12)
        by_phone = {s.phone: s for s in staff}
        if DEMO_VET_PHONE not in by_phone:
            from src.auth.deps import hash_password
            vet = Staff(
                centre_id=centres[0].id, name="Demo Vet", role="vet",
                phone=DEMO_VET_PHONE, password_hash=hash_password(demo_password), active=True,
            )
            db.add(vet)
            await db.flush()
            by_phone[DEMO_VET_PHONE] = vet
        if DEMO_SURGEON_PHONE not in by_phone:
            from src.auth.deps import hash_password
            surgeon = Staff(
                centre_id=centres[1].id, name="Demo Surgeon", role="surgeon",
                phone=DEMO_SURGEON_PHONE, password_hash=hash_password(demo_password), active=True,
            )
            db.add(surgeon)
            await db.flush()
            by_phone[DEMO_SURGEON_PHONE] = surgeon

        if "9999999999" not in by_phone:
            from src.auth.deps import hash_password
            admin = Staff(
                centre_id=None, name="Demo Admin", role="admin",
                phone="9999999999", password_hash=hash_password(demo_password), active=True,
            )
            db.add(admin)
            await db.commit()
            print(f"Seeded demo admin: phone 9999999999 / generated_password={demo_password}")

        vet = by_phone[DEMO_VET_PHONE]
        surgeon = by_phone[DEMO_SURGEON_PHONE]
        admin = next((s for s in staff if s.role == "admin"), None)
        inspector_id = admin.id if admin else vet.id

        # Clear demo-scoped tables (order matters for FK constraints)
        for model in (Expense, Allocation, Grant, Inspection, Surgery, Dog):
            await db.execute(delete(model))
        await db.commit()

        now = datetime.now(UTC).replace(tzinfo=None)
        fy = state_financial_year()
        fy_prev = f"{int(fy[:4]) - 1}-{fy[2:4]}"

        # ─── Grants (10, AWBI-style refs) ───────────────────────────────────
        grant_specs = [
            ("AWBI/2026/GR/0038", Decimal("500000.00"), "Sterilization programme Q1", fy),
            ("AWBI/2026/GR/0042", Decimal("250000.00"), "Sterilization programme Q2", fy),
            ("AWBI/2026/GR/0051", Decimal("120000.00"), "Infrastructure upgrade", fy),
            ("AWBI/2026/GR/0057", Decimal("180000.00"), "Anti-rabies vaccination drive", fy),
            ("AWBI/2026/GR/0064", Decimal("75000.00"), "Emergency medical equipment", fy),
            ("AWBI/2025/GR/0091", Decimal("300000.00"), "Feeding programme support", fy_prev),
            ("AWBI/2025/GR/0103", Decimal("140000.00"), "Staff training & capacity building", fy_prev),
            ("AWBI/2025/GR/0112", Decimal("60000.00"), "Sterilization programme Q3", fy_prev),
            ("AWBI/2024/GR/0148", Decimal("90000.00"), "Infrastructure upgrade", "2024-25"),
            ("AWBI/2024/GR/0155", Decimal("110000.00"), "Vaccination drive", "2024-25"),
        ]
        grants = []
        for ref, amount, purpose, year in grant_specs:
            g = Grant(awbi_ref=ref, amount=amount, purpose=purpose, financial_year=year, status="active")
            db.add(g)
            grants.append(g)
        await db.flush()
        for g in grants:
            await db.refresh(g)

        # ─── Allocations (a subset of centres, spread across active grants) ──
        alloc_centres = random.sample(centres, min(15, len(centres)))
        allocations = []
        grant_budget = {g.id: float(g.amount) for g in grants[:6]}  # allocate from recent grants
        for centre in alloc_centres:
            grant = random.choice(grants[:6])
            # Allocate 20-60% of grant budget per centre, never exceeding budget
            alloc_amt = min(Decimal(random.randint(20000, 80000)), Decimal(str(grant_budget[grant.id])))
            grant_budget[grant.id] -= float(alloc_amt)
            if grant_budget[grant.id] < 0:
                continue
            alloc = Allocation(
                grant_id=grant.id, centre_id=centre.id, amount=alloc_amt,
                allocated_at=now - timedelta(days=random.randint(5, 90)),
            )
            db.add(alloc)
            allocations.append(alloc)
        await db.flush()
        for a in allocations:
            await db.refresh(a)

        # ─── Dogs (~180) across centres ──────────────────────────────────────
        dogs = []
        dog_centres = random.sample(centres, min(40, len(centres)))
        tag_prefix = {c.id: "".join(ch for ch in c.code if ch.isalnum())[:3].upper() for c in centres}
        for ci, centre in enumerate(dog_centres):
            n = random.randint(3, 6)
            for _ in range(n):
                dogs.append(Dog(
                    centre_id=centre.id,
                    tag_id=f"{tag_prefix[centre.id]}-{random.randint(1000, 9999)}",
                    sex=random.choice(["F", "F", "M"]),
                    age_estimate=random.randint(1, 6),
                    weight=round(random.uniform(8.0, 24.0), 1),
                    status=random.choice(["registered", "registered", "registered", "adopted"]),
                ))
        db.add_all(dogs)
        await db.flush()
        for d in dogs:
            await db.refresh(d)

        # ─── Surgeries (~180, last 6 months) ─────────────────────────────────
        surgeries = []
        for dog in dogs:
            n_surge = random.randint(1, 2)
            for _ in range(n_surge):
                surgeries.append(Surgery(
                    dog_id=dog.id,
                    centre_id=dog.centre_id,
                    staff_id=random.choice([vet.id, surgeon.id]),
                    surgery_type=random.choice(SURGERY_TYPES),
                    weight=dog.weight,
                    complications=random.choice(COMPLICATIONS_POOL),
                    timestamp=now - timedelta(days=random.randint(0, 180), hours=random.randint(1, 10)),
                ))
        db.add_all(surgeries)
        await db.flush()
        for s in surgeries:
            await db.refresh(s)

        # ─── Inspections (~80, quarterly cycle over 12 months) ───────────────
        inspections = []
        insp_centres = random.sample(centres, min(30, len(centres)))
        for centre in insp_centres:
            for quarter in range(4):
                status = random.choice(["completed", "completed", "completed", "scheduled", "overdue"])
                if status == "completed":
                    scheduled = now - timedelta(days=random.randint(10, 360))
                    conducted = scheduled + timedelta(days=random.randint(0, 5))
                    findings = random.choice(FINDINGS_POOL)
                else:
                    scheduled = now + timedelta(days=random.randint(-7, 45))
                    conducted = None
                    findings = None
                inspections.append(Inspection(
                    centre_id=centre.id, inspector_id=inspector_id, status=status,
                    scheduled_at=scheduled, conducted_at=conducted, findings=findings,
                ))
        db.add_all(inspections)

        # ─── Expenses (~90 across allocations) ───────────────────────────────
        expenses = []
        for alloc in allocations:
            n_exp = random.randint(4, 9)
            alloc_remaining = float(alloc.amount)
            for _ in range(n_exp):
                if alloc_remaining <= 0:
                    break
                amount = min(Decimal(random.randint(500, 12000)), Decimal(str(alloc_remaining)))
                alloc_remaining -= float(amount)
                expenses.append(Expense(
                    allocation_id=alloc.id,
                    surgery_id=random.choice(surgeries).id if surgeries else None,
                    category=random.choice(EXPENSE_CATEGORIES),
                    amount=amount,
                    bill_ref=f"BILL/2026/{random.randint(1000, 9999)}",
                    expense_at=date.today() - timedelta(days=random.randint(0, 90)),
                ))
        db.add_all(expenses)
        await db.commit()

    print(
        f"Seeded: {len(grants)} grants, {len(allocations)} allocations, {len(expenses)} expenses, "
        f"{len(dogs)} dogs, {len(surgeries)} surgeries, {len(inspections)} inspections"
    )

    # ─── Committee governance data (Committee Portal) ───
    async with async_session() as db:
        existing = (await db.execute(select(Committee))).scalars().first()
        if existing:
            print("Committee data already present — skipping committee seed")
            return

        committee = Committee(
            name="State Animal Welfare Board — Governing Body",
            description="Oversight committee for the state ABC programme",
        )
        db.add(committee)
        await db.flush()

        staff_all = list((await db.execute(select(Staff))).scalars())
        member_roles = ["chair", "secretary", "member", "member", "member"]
        members = []
        for i, role in enumerate(member_roles):
            staff = staff_all[i % len(staff_all)] if staff_all else None
            member = CommitteeMember(
                committee_id=committee.id,
                member_id=staff.id if staff else str(i),
                role=role,
            )
            db.add(member)
            members.append(member)
        await db.flush()

        # Meetings: two past, three upcoming
        now = datetime.now(UTC).replace(tzinfo=None)
        meeting_specs = [
            ("Quarterly Review Board", now - timedelta(days=45), "completed", "Board Hall, Jaipur"),
            ("ABC Programme Mid-Year Review", now - timedelta(days=12), "completed", "Virtual"),
            ("Quarterly Review Board", now + timedelta(days=10), "scheduled", "Board Hall, Jaipur"),
            ("Policy Draft Committee", now + timedelta(days=21), "scheduled", "Virtual"),
            ("Annual General Body", now + timedelta(days=48), "scheduled", "RC Convention Centre"),
        ]
        meetings = []
        for title, when, status, location in meeting_specs:
            m = Meeting(
                committee_id=committee.id, title=title, scheduled_at=when,
                duration_minutes=120 if "Review" in title else 60,
                location=location,
                meeting_type="virtual" if location == "Virtual" else "in-person",
                status=status,
            )
            db.add(m)
            meetings.append(m)
        await db.flush()

        # Decisions: passed / rejected / pending with realistic tallies
        decision_specs = [
            ("RES-2026-014", "Data Retention Policy Amendment", "passed", 9, 2, 1),
            ("RES-2026-013", "Q3 Audit Framework Approval", "rejected", 4, 7, 1),
            ("RES-2026-012", "Vendor Risk Assessment Guidelines", "pending", 0, 0, 0),
            ("RES-2026-011", "Surgeon Empanelment Expansion", "passed", 11, 1, 0),
        ]
        for res_id, subject, status, yes, no, abstain in decision_specs:
            d = Decision(
                meeting_id=meetings[0].id if status != "pending" else meetings[2].id,
                resolution_id=res_id,
                subject=subject,
                status=status,
                decided_at=now - timedelta(days=40) if status != "pending" else None,
            )
            db.add(d)
            await db.flush()
            for k in range(yes):
                db.add(Vote(decision_id=d.id, member_id=str(k), vote="yes", voted_at=d.decided_at))
            for k in range(no):
                db.add(Vote(decision_id=d.id, member_id=str(100 + k), vote="no", voted_at=d.decided_at))
            for k in range(abstain):
                db.add(Vote(decision_id=d.id, member_id=str(200 + k), vote="abstain", voted_at=d.decided_at))

        docs = [
            ("Draft_Policy_v4.pdf", "pdf", 842_133),
            ("Q3_Minutes_Final.pdf", "pdf", 331_002),
            ("Fund_Utilisation_Certificate_Q2.xlsx", "xlsx", 45_880),
            ("AWBI_Grant_Sanction_Letter.pdf", "pdf", 1_204_551),
        ]
        for title, ftype, size in docs:
            db.add(CommitteeDocument(
                committee_id=committee.id, title=title, file_type=ftype,
                file_size=size, file_path=f"/documents/{title}",
                uploaded_by=staff_all[0].id if staff_all else "system",
            ))

        await db.commit()
        print("Committee seeded: 1 committee, 5 members, 5 meetings, 4 decisions, 4 documents")
    print(f"Demo staff: vet={DEMO_VET_PHONE}, surgeon={DEMO_SURGEON_PHONE} "
          f"(shared generated password printed above for the admin; set DEMO_PASSWORD to fix it)")

if __name__ == "__main__":
    asyncio.run(seed())
