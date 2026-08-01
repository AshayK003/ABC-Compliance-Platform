from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Inspection

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
    _: TokenPayload = Depends(require_role("admin", "vet")),
):
    inspection = Inspection(**body.model_dump())
    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)
    return inspection


@router.get("")
async def list_inspections(
    centre_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    stmt = select(Inspection).order_by(Inspection.scheduled_at.desc()).limit(limit).offset(offset)
    if centre_id:
        stmt = stmt.where(Inspection.centre_id == centre_id)
    if status:
        stmt = stmt.where(Inspection.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{inspection_id}")
async def get_inspection(
    inspection_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Inspection).where(Inspection.id == inspection_id))
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection
