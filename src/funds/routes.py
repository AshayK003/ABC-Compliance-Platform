from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Allocation, Expense, Grant

router = APIRouter(prefix="/grants", tags=["grants"])


class GrantCreate(BaseModel):
    awbi_ref: str
    amount: float
    purpose: str
    financial_year: str
    status: str = "active"


@router.post("", status_code=201)
async def create_grant(
    body: GrantCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    grant = Grant(**body.model_dump())
    db.add(grant)
    await db.commit()
    await db.refresh(grant)
    return grant


@router.get("")
async def list_grants(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Grant).order_by(Grant.financial_year.desc()))
    return result.scalars().all()


@router.get("/{grant_id}")
async def get_grant(
    grant_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Grant).where(Grant.id == grant_id))
    grant = result.scalar_one_or_none()
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")
    return grant


# ─── Allocations ───

alloc_router = APIRouter(prefix="/allocations", tags=["allocations"])


class AllocationCreate(BaseModel):
    grant_id: str
    centre_id: str
    amount: float


@alloc_router.post("", status_code=201)
async def create_allocation(
    body: AllocationCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    allocation = Allocation(
        **body.model_dump(),
        allocated_at=datetime.now(UTC),
    )
    db.add(allocation)
    await db.commit()
    await db.refresh(allocation)
    return allocation


@alloc_router.get("")
async def list_allocations(
    grant_id: str | None = Query(None),
    centre_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    stmt = select(Allocation).order_by(Allocation.allocated_at.desc())
    if grant_id:
        stmt = stmt.where(Allocation.grant_id == grant_id)
    if centre_id:
        stmt = stmt.where(Allocation.centre_id == centre_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@alloc_router.get("/{allocation_id}")
async def get_allocation(
    allocation_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Allocation).where(Allocation.id == allocation_id))
    allocation = result.scalar_one_or_none()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return allocation


# ─── Expenses ───

exp_router = APIRouter(prefix="/expenses", tags=["expenses"])


class ExpenseCreate(BaseModel):
    allocation_id: str
    surgery_id: str | None = None
    category: str
    amount: float
    bill_ref: str | None = None
    expense_at: datetime | None = None


@exp_router.post("", status_code=201)
async def create_expense(
    body: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet")),
):
    expense = Expense(
        **body.model_dump(exclude_none=True),
        expense_at=body.expense_at or datetime.now(UTC).date(),
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


@exp_router.get("")
async def list_expenses(
    allocation_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    stmt = select(Expense).order_by(Expense.expense_at.desc())
    if allocation_id:
        stmt = stmt.where(Expense.allocation_id == allocation_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@exp_router.get("/{expense_id}")
async def get_expense(
    expense_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense
