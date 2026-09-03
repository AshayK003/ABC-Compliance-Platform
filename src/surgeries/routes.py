from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.routes import log_audit_event
from src.auth.deps import (
    TokenPayload,
    check_centre_read,
    get_current_user,
    require_centre_access,
    require_role,
    scope_centre_filter,
)
from src.database import get_db
from src.models.base import Centre, Dog, Staff, Surgery
from src.utils.fk import assert_fk_exists

router = APIRouter(prefix="/surgeries", tags=["surgeries"])


class SurgeryCreate(BaseModel):
    dog_id: str
    centre_id: str
    staff_id: str
    surgery_type: str = Field(min_length=1, max_length=100)
    weight: float | None = Field(default=None, ge=0)
    complications: str | None = None
    timestamp: datetime | None = None


@router.post("", status_code=201)
async def create_surgery(
    body: SurgeryCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_centre_access("centre_id")),
    user: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    dog = await assert_fk_exists(db, Dog, body.dog_id, "dog")
    await assert_fk_exists(db, Centre, body.centre_id, "centre")
    staff = await assert_fk_exists(db, Staff, body.staff_id, "staff")
    # Same-centre linkage: a surgery must not join a dog/staff from another
    # centre. (None = optional FK or test double; real mismatches are 400.)
    if dog is not None and dog.centre_id != body.centre_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="dog_id belongs to a different centre")
    if staff is not None and staff.centre_id is not None and staff.centre_id != body.centre_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="staff_id belongs to a different centre")
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
    await log_audit_event(db, "surgery", surgery.id, "create", actor_id=user.user_id)
    return surgery


@router.get("")
async def list_surgeries(
    centre_id: str | None = Query(None),
    dog_id: str | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    centre_id = scope_centre_filter(current, centre_id)
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
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Surgery).where(Surgery.id == surgery_id))
    surgery = result.scalar_one_or_none()
    if not surgery:
        raise HTTPException(status_code=404, detail="Surgery not found")
    check_centre_read(current, surgery.centre_id)
    return surgery
