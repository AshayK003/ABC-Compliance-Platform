from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
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
from src.models.base import Centre, Inspection, Staff
from src.utils.fk import assert_fk_exists

router = APIRouter(prefix="/inspections", tags=["inspections"])


class InspectionCreate(BaseModel):
    centre_id: str
    inspector_id: str
    scheduled_at: datetime | None = None
    status: str = "scheduled"


@router.post("", status_code=201)
async def create_inspection(
    body: InspectionCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_centre_access("centre_id")),
    user: TokenPayload = Depends(require_role("admin", "vet")),
):
    await assert_fk_exists(db, Centre, body.centre_id, "centre")
    inspector = await assert_fk_exists(db, Staff, body.inspector_id, "inspector")
    # Same-centre linkage: the inspector must belong to the inspected centre
    # (unless unassigned). None = test double; real mismatches are 400.
    if inspector is not None and inspector.centre_id is not None and inspector.centre_id != body.centre_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="inspector_id belongs to a different centre")
    inspection = Inspection(**body.model_dump())
    db.add(inspection)
    try:
        await db.commit()
        await db.refresh(inspection)
    except Exception as e:
        await db.rollback()
        if "foreign" in str(e).lower() or "centre" in str(e).lower() or "inspector" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid centre_id or inspector_id")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Inspection creation failed")
    await log_audit_event(db, "inspection", inspection.id, "create", actor_id=user.user_id)
    return inspection


@router.get("")
async def list_inspections(
    centre_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    centre_id = scope_centre_filter(current, centre_id)
    stmt = select(Inspection).order_by(Inspection.scheduled_at.desc()).limit(limit).offset(offset)
    if centre_id:
        stmt = stmt.where(Inspection.centre_id == centre_id)
    if status:
        stmt = stmt.where(Inspection.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{inspection_id}", responses={404: {"description": "Inspection not found"}})
async def get_inspection(
    inspection_id: str,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Inspection).where(Inspection.id == inspection_id))
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    check_centre_read(current, inspection.centre_id)
    return inspection
