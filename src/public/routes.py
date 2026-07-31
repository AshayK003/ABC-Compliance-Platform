from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Complaint, SyncQueue

# ─── Public Complaints Router ───
public_router = APIRouter(prefix="/public", tags=["public"])

class ComplaintCreate(BaseModel):
    centre_id: str
    citizen_phone: str
    description: str


class ComplaintUpdate(BaseModel):
    status: str
    resolution: str | None = None


@public_router.post("/complaints", status_code=status.HTTP_201_CREATED)
async def create_complaint(
    body: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
):
    complaint = Complaint(**body.model_dump())
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return complaint


@public_router.get("/complaints")
async def list_complaints(
    centre_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    stmt = select(Complaint).order_by(Complaint.created_at.desc())
    if centre_id:
        stmt = stmt.where(Complaint.centre_id == centre_id)
    if status:
        stmt = stmt.where(Complaint.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@public_router.get("/complaints/{complaint_id}")
async def get_complaint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@public_router.patch("/complaints/{complaint_id}")
async def update_complaint(
    complaint_id: str,
    body: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
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


# ─── Sync Queue Router ───
sync_router = APIRouter(prefix="/sync", tags=["sync"])


class SyncEnqueue(BaseModel):
    entity_type: str
    entity_id: str
    operation: str  # create, update, delete
    payload: dict
    idempotency_key: str


@sync_router.post("/enqueue", status_code=status.HTTP_200_OK)
async def enqueue_sync(
    body: SyncEnqueue,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    # Check idempotency
    result = await db.execute(
        select(SyncQueue).where(SyncQueue.idempotency_key == body.idempotency_key)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {
            "id": existing.id,
            "entity_type": existing.entity_type,
            "entity_id": existing.entity_id,
            "operation": existing.operation,
            "payload": json.loads(str(existing.payload)) if existing.payload else {},
            "idempotency_key": existing.idempotency_key,
            "status": existing.status,
            "retry_count": existing.retry_count,
            "created_at": existing.created_at,
            "synced_at": existing.synced_at,
            "error": existing.error,
        }

    item = SyncQueue(
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        operation=body.operation,
        payload=json.dumps(body.payload),
        idempotency_key=body.idempotency_key,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@sync_router.get("/pending")
async def list_pending_sync(
    entity_type: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    stmt = (
        select(SyncQueue)
        .where(SyncQueue.status == "pending")
        .order_by(SyncQueue.created_at)
        .limit(limit)
    )
    if entity_type:
        stmt = stmt.where(SyncQueue.entity_type == entity_type)

    result = await db.execute(stmt)
    return result.scalars().all()


@sync_router.post("/mark-synced/{sync_id}")
async def mark_synced(
    sync_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.id == sync_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Sync item not found")

    item.status = "synced"
    item.synced_at = datetime.utcnow()
    await db.commit()
    return item


@sync_router.post("/mark-failed/{sync_id}")
async def mark_failed(
    sync_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.id == sync_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Sync item not found")

    item.status = "failed"
    item.error = body.get("error", "Unknown error")
    item.retry_count += 1
    await db.commit()
    return item


@sync_router.post("/retry-failed")
async def retry_failed(
    max_retries: int = 3,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(
        select(SyncQueue).where(SyncQueue.status == "failed", SyncQueue.retry_count < max_retries)
    )
    items = result.scalars().all()
    count = 0
    for item in items:
        item.status = "pending"
        item.error = None
        count += 1
    await db.commit()
    return {"retried": count}


@sync_router.get("/status/{idempotency_key}")
async def sync_status(
    idempotency_key: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.idempotency_key == idempotency_key))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Sync item not found")
    return item
