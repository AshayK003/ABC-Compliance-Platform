from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Centre, Staff

router = APIRouter(prefix="/centres", tags=["centres"])


class CentreCreate(BaseModel):
    name: str
    code: str
    district: str
    state: str
    capacity: int = 0


class CentreOut(BaseModel):
    id: str
    name: str
    code: str
    district: str
    state: str
    capacity: int
    status: str
    staff_count: int = 0


@router.get("")
async def list_centres(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # Subquery for staff count per centre to avoid N+1
    staff_count_subq = (
        select(Staff.centre_id, func.count(Staff.id).label("staff_count"))
        .where(Staff.centre_id.is_not(None))
        .group_by(Staff.centre_id)
        .subquery()
    )

    result = await db.execute(
        select(Centre, staff_count_subq.c.staff_count)
        .outerjoin(staff_count_subq, Centre.id == staff_count_subq.c.centre_id)
        .order_by(Centre.name)
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()
    return [
        CentreOut(
            id=c.id,
            name=c.name,
            code=c.code,
            district=c.district,
            state=c.state,
            capacity=c.capacity,
            status=c.status,
            staff_count=staff_count or 0,
        )
        for c, staff_count in rows
    ]


@router.post("", status_code=201)
async def create_centre(
    body: CentreCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    centre = Centre(**body.model_dump())
    db.add(centre)
    await db.commit()
    await db.refresh(centre)
    return centre


@router.get("/{centre_id}")
async def get_centre(
    centre_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Centre).where(Centre.id == centre_id))
    centre = result.scalar_one_or_none()
    if not centre:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    return centre


@router.get("/{centre_id}/staff")
async def list_centre_staff(
    centre_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(
        select(Staff).where(Staff.centre_id == centre_id).order_by(Staff.name)
    )
    return result.scalars().all()
