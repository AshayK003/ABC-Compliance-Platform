from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.routes import log_audit_event
from src.auth.deps import (
    TokenPayload,
    check_centre_read,
    get_current_user,
    require_role,
    scope_centre_filter,
)
from src.database import get_db
from src.models.base import Allocation, Centre, Expense, Grant, Surgery
from src.utils.fk import assert_fk_exists

router = APIRouter(prefix="/grants", tags=["grants"])


class GrantCreate(BaseModel):
    awbi_ref: str
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    purpose: str
    financial_year: str
    status: str = "active"


@router.post("", status_code=201)
async def create_grant(
    body: GrantCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role("admin")),
):
    grant = Grant(**body.model_dump())
    db.add(grant)
    try:
        await db.commit()
        await db.refresh(grant)
    except Exception as e:
        await db.rollback()
        if "unique" in str(e).lower() or "awbi_ref" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Grant reference already exists")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Grant creation failed")
    await log_audit_event(db, "grant", grant.id, "create", actor_id=user.user_id)
    return grant


@router.get("")
async def list_grants(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Grant).order_by(Grant.financial_year.desc()))
    return result.scalars().all()


@router.get("/{grant_id}", responses={404: {"description": "Grant not found"}})
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
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


@alloc_router.post("", status_code=201)
async def create_allocation(
    body: AllocationCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role("admin")),
):
    await assert_fk_exists(db, Centre, body.centre_id, "centre")
    grant = await assert_fk_exists(db, Grant, body.grant_id, "grant")
    if grant is not None:
        # Grant-level balance guard: allocations must never exceed the grant.
        # (None = unconfigured test double; real rows are Grant instances.)
        existing_result = await db.execute(
            select(func.sum(Allocation.amount)).where(Allocation.grant_id == body.grant_id)
        )
        total_allocated = existing_result.scalar() or Decimal("0")
        if total_allocated + body.amount > grant.amount:
            available = grant.amount - total_allocated
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Allocation exceeds grant balance. "
                    f"Available: {available}, Requested: {body.amount}"
                ),
            )
    allocation = Allocation(
        **body.model_dump(),
    )
    db.add(allocation)
    try:
        await db.commit()
        await db.refresh(allocation)
    except Exception as e:
        await db.rollback()
        if "foreign" in str(e).lower() or "grant" in str(e).lower() or "centre" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid grant_id or centre_id")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Allocation creation failed")
    await log_audit_event(db, "allocation", allocation.id, "create", actor_id=user.user_id)
    return allocation


@alloc_router.get("")
async def list_allocations(
    grant_id: str | None = Query(None),
    centre_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    centre_id = scope_centre_filter(current, centre_id)
    stmt = select(Allocation).order_by(Allocation.allocated_at.desc()).limit(limit).offset(offset)
    if grant_id:
        stmt = stmt.where(Allocation.grant_id == grant_id)
    if centre_id:
        stmt = stmt.where(Allocation.centre_id == centre_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@alloc_router.get("/{allocation_id}", responses={404: {"description": "Allocation not found"}})
async def get_allocation(
    allocation_id: str,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Allocation).where(Allocation.id == allocation_id))
    allocation = result.scalar_one_or_none()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    check_centre_read(current, allocation.centre_id)
    return allocation


# ─── Expenses ───

exp_router = APIRouter(prefix="/expenses", tags=["expenses"])


class ExpenseCreate(BaseModel):
    allocation_id: str
    surgery_id: str | None = None
    category: str
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    bill_ref: str | None = None
    expense_at: datetime | None = None


@exp_router.post(
    "",
    status_code=201,
    responses={
        404: {"description": "Allocation not found"},
        400: {"description": "Expense exceeds allocation balance"},
    },
)
async def create_expense(
    body: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role("admin", "vet")),
):
    # Lock the allocation row for the duration of the transaction so two
    # concurrent expenses cannot both pass the balance check (TOCTOU race).
    allocation_result = await db.execute(
        select(Allocation).where(Allocation.id == body.allocation_id).with_for_update()
    )
    allocation = allocation_result.scalar_one_or_none()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    # Object-level authorization (anti-IDOR): non-admin staff may only bill
    # against allocations belonging to their own centre.
    if user.role != "admin" and allocation.centre_id != user.centre_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: allocation belongs to another centre",
        )

    # Sum existing expenses for this allocation
    existing_expenses_result = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.allocation_id == body.allocation_id)
    )
    total_existing = existing_expenses_result.scalar() or Decimal("0")

    if total_existing + body.amount > allocation.amount:
            available = allocation.amount - total_existing
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Expense exceeds allocation balance. "
                    f"Available: {available}, Requested: {body.amount}"
                ),
            )

    # Same-centre linkage: a linked surgery must belong to the allocation's centre.
    if body.surgery_id:
        surgery = await assert_fk_exists(db, Surgery, body.surgery_id, "surgery")
        if surgery is not None and surgery.centre_id != allocation.centre_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="surgery_id belongs to a different centre than the allocation",
            )

    # Expense.expense_at is a Date column; accept datetimes at the API boundary.
    expense_at = body.expense_at.date() if isinstance(body.expense_at, datetime) else body.expense_at
    expense_data = body.model_dump(exclude_none=True, exclude={"expense_at"})
    if expense_at is not None:
        expense_data["expense_at"] = expense_at
    expense = Expense(**expense_data)
    db.add(expense)
    try:
        await db.commit()
        await db.refresh(expense)
    except Exception as e:
        await db.rollback()
        if "foreign" in str(e).lower() or "allocation" in str(e).lower() or "surgery" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid allocation_id or surgery_id")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Expense creation failed")
    await log_audit_event(db, "expense", expense.id, "create", actor_id=user.user_id)
    return expense


@exp_router.get("")
async def list_expenses(
    allocation_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    stmt = select(Expense).order_by(Expense.expense_at.desc()).limit(limit).offset(offset)
    if current.role != "admin":
        # Expenses carry no centre_id of their own: scope via the allocation.
        if not current.centre_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: no centre assigned to this account",
            )
        stmt = stmt.join(Allocation, Expense.allocation_id == Allocation.id).where(
            Allocation.centre_id == current.centre_id
        )
    if allocation_id:
        stmt = stmt.where(Expense.allocation_id == allocation_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@exp_router.get("/{expense_id}", responses={404: {"description": "Expense not found"}})
async def get_expense(
    expense_id: str,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current.role != "admin":
        alloc_result = await db.execute(select(Allocation).where(Allocation.id == expense.allocation_id))
        allocation = alloc_result.scalar_one_or_none()
        check_centre_read(current, allocation.centre_id if isinstance(allocation, Allocation) else None)
    return expense
