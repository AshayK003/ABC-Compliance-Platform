from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.base import Complaint

router = APIRouter(prefix="/complaints", tags=["complaints"])


class ComplaintCreate(BaseModel):
    centre_id: str
    citizen_phone: str
    description: str


class ComplaintUpdate(BaseModel):
    status: str
    resolution: str | None = None


class MarkFailedRequest(BaseModel):
    error: str


VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_complaint(
    body: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
):
    complaint = Complaint(
        **body.model_dump(),
        status="open",
        created_at=datetime.now(UTC),
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return complaint


@router.get("")
async def list_complaints(
    centre_id: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Complaint).order_by(Complaint.created_at.desc())
    if centre_id:
        stmt = stmt.where(Complaint.centre_id == centre_id)
    if status:
        stmt = stmt.where(Complaint.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{complaint_id}")
async def get_complaint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.patch("/{complaint_id}")
async def update_complaint(
    complaint_id: str,
    body: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")

    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = body.status
    if body.resolution:
        complaint.resolution = body.resolution
    await db.commit()
    await db.refresh(complaint)
    return complaint
