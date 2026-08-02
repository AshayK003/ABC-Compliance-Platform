from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.cache import cache, cache_key, invalidate_pattern
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
    # Cache key includes pagination params
    cache_k = cache_key("centres", "list", f"limit={limit}", f"offset={offset}")
    cached_data = cache.get(cache_k)
    if cached_data is not None:
        return cached_data

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
    data = [
        {
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "district": c.district,
            "state": c.state,
            "capacity": c.capacity,
            "status": c.status,
            "staff_count": staff_count or 0,
        }
        for c, staff_count in rows
    ]
    cache.set(cache_k, data)
    return data


@router.post("", status_code=201)
async def create_centre(
    body: CentreCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    centre = Centre(**body.model_dump())
    db.add(centre)
    try:
        await db.commit()
        await db.refresh(centre)
    except Exception as e:
        await db.rollback()
        if "code" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Centre code already exists")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Centre creation failed")
    # Invalidate cache
    invalidate_pattern("centres:")
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
