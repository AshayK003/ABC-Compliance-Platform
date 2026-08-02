from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Surgery

router = APIRouter(prefix="/surgeries", tags=["surgeries"])


class SurgeryCreate(BaseModel):
    dog_id: str
    centre_id: str
    staff_id: str
    surgery_type: str
    weight: float | None = None
    complications: str | None = None
    timestamp: datetime | None = None


@router.post("", status_code=201)
async def create_surgery(
    body: SurgeryCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    surgery = Surgery(**body.model_dump(exclude_none=True))
    db.add(surgery)
    try:
        await db.commit()
        await db.refresh(surgery)
    except Exception as e:
        await db.rollback()
        if "foreign" in str(e).lower() or "dog" in str(e).lower() or "centre" in str(e).lower() or "staff" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid dog_id, centre_id, or staff_id")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Surgery creation failed")
    return surgery


@router.get("")
async def list_surgeries(
    centre_id: str | None = Query(None),
    dog_id: str | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    stmt = select(Surgery).order_by(Surgery.timestamp.desc()).limit(limit).offset(offset)

    if centre_id:
        stmt = stmt.where(Surgery.centre_id == centre_id)
    if dog_id:
        stmt = stmt.where(Surgery.dog_id == dog_id)
    if from_date:
        stmt = stmt.where(Surgery.timestamp >= from_date)
    if to_date:
        stmt = stmt.where(Surgery.timestamp <= to_date)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{surgery_id}", responses={404: {"description": "Surgery not found"}})
async def get_surgery(
    surgery_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Surgery).where(Surgery.id == surgery_id))
    surgery = result.scalar_one_or_none()
    if not surgery:
        raise HTTPException(status_code=404, detail="Surgery not found")
    return surgery
