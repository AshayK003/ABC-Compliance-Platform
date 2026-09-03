from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import (
    TokenPayload,
    check_centre_read,
    get_current_user,
    require_role,
    scope_centre_filter,
)
from src.database import get_db
from src.models.base import Centre, Complaint, Inspection, SyncQueue
from src.ratelimit import limiter as public_limiter
from src.utils.fk import assert_fk_exists

# Rate limiter for public endpoints (shared instance; see src/ratelimit.py).

# ─── Public Complaints Router ───
public_router = APIRouter(prefix="/public", tags=["public"])


class ComplaintCreate(BaseModel):
    centre_id: str
    citizen_phone: str = Field(min_length=10, max_length=15)
    description: str = Field(min_length=1)


class ComplaintUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved", "closed"]
    resolution: str | None = None


@public_router.post(
    "/complaints",
    status_code=status.HTTP_201_CREATED,
    responses={400: {"description": "Invalid centre_id"}},
)
@public_limiter.limit("10/hour")
async def create_complaint(
    request: Request,
    body: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
):
    await assert_fk_exists(db, Centre, body.centre_id, "centre")
    complaint = Complaint(**body.model_dump())
    db.add(complaint)
    try:
        await db.commit()
        await db.refresh(complaint)
    except Exception as e:
        await db.rollback()
        # centre_id was already validated above: only FK-shaped failures map
        # to 400. Anything else (DB down, constraint bug) is a genuine 500 —
        # misreporting it as "invalid centre" hides outages from monitoring.
        if "foreign" in str(e).lower() or "centre" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid centre_id: no such centre",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Complaint submission failed",
        )
    return complaint


@public_router.get("/complaints")
async def list_complaints(
    centre_id: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    centre_id = scope_centre_filter(current, centre_id)
    stmt = select(Complaint).order_by(Complaint.created_at.desc()).limit(limit).offset(offset)
    if centre_id:
        stmt = stmt.where(Complaint.centre_id == centre_id)
    if status:
        stmt = stmt.where(Complaint.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@public_router.get(
    "/complaints/{complaint_id}",
    responses={404: {"description": "Complaint not found"}},
)
async def get_complaint(
    complaint_id: str,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    check_centre_read(current, complaint.centre_id)
    return complaint


@public_router.patch(
    "/complaints/{complaint_id}",
    responses={404: {"description": "Complaint not found"}},
)
async def update_complaint(
    complaint_id: str,
    body: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    check_centre_read(current, complaint.centre_id)

    complaint.status = body.status
    if body.resolution:
        complaint.resolution = body.resolution
    await db.commit()
    await db.refresh(complaint)
    return complaint


# ─── Compliance Heatmap ───
class HeatmapState(BaseModel):
    state: str
    centres: int
    inspections: int
    compliance_rate: float
    risk: str  # critical, moderate, compliant


def _risk_for_rate(rate: float) -> str:
    """Map a compliance rate (0-100) to a risk level."""
    if rate < 50:
        return "critical"
    if rate < 80:
        return "moderate"
    return "compliant"


def _seed_state_stats(centres) -> tuple[dict[str, dict], dict[str, str]]:
    """Start state aggregates from ALL centres so states with no inspections still appear."""
    state_stats: dict[str, dict] = {}
    centre_state_map: dict[str, str] = {}
    for c in centres:
        if not c.state:
            continue
        centre_state_map[c.id] = c.state
        if c.state not in state_stats:
            state_stats[c.state] = {"total": 0, "completed": 0, "centres": set()}
        state_stats[c.state]["centres"].add(c.id)
    return state_stats, centre_state_map


def _overlay_inspections(
    state_stats: dict[str, dict],
    centre_state_map: dict[str, str],
    ins_data,
) -> None:
    """Add inspection counts onto the per-state aggregates."""
    for centre_id, status_val, count in ins_data:
        state = centre_state_map.get(centre_id)
        if not state or state not in state_stats:
            continue
        state_stats[state]["total"] += count
        if status_val == "completed":
            state_stats[state]["completed"] += count


def _build_heatmap_result(state_stats: dict[str, dict]) -> list[HeatmapState]:
    """Convert per-state aggregates into the response model, sorted critical-first."""
    result = []
    for state, stats in state_stats.items():
        total_inspections = stats["total"]
        compliance_rate = (stats["completed"] / total_inspections * 100) if total_inspections > 0 else 0
        result.append(HeatmapState(
            state=state,
            centres=len(stats["centres"]),
            inspections=total_inspections,
            compliance_rate=round(compliance_rate, 1),
            risk=_risk_for_rate(compliance_rate),
        ))
    risk_order = {"critical": 0, "moderate": 1, "compliant": 2}
    result.sort(key=lambda x: (risk_order.get(x.risk, 3), x.state))
    return result


@public_router.get("/heatmap", response_model=list[HeatmapState])
async def compliance_heatmap(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    """
    Aggregate compliance by state for the heatmap.
    Compliance = inspections with status='completed' / total inspections per state.
    """
    # Get centres with their states
    centres_stmt = select(Centre.id, Centre.state).where(Centre.state.isnot(None))
    centres_result = await db.execute(centres_stmt)
    centres = centres_result.all()

    if not centres:
        return []

    state_stats, centre_state_map = _seed_state_stats(centres)

    # Get inspection counts by centre
    ins_stmt = (
        select(Inspection.centre_id, Inspection.status, func.count(Inspection.id))
        .where(Inspection.centre_id.in_(centre_state_map.keys()))
        .group_by(Inspection.centre_id, Inspection.status)
    )
    ins_result = await db.execute(ins_stmt)
    ins_data = ins_result.all()

    _overlay_inspections(state_stats, centre_state_map, ins_data)

    return _build_heatmap_result(state_stats)


@public_router.get("/compliance-scores")
async def compliance_scores(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    """Real compliance score per centre: completed inspections / total inspections.

    This is the number the dashboard's 'Compliance >90%' card reports on —
    it must be the genuine ratio, not a binary has-any-completed-inspection flag.
    """
    centres_result = await db.execute(select(Centre))
    centres = centres_result.scalars().all()

    ins_stmt = (
        select(Inspection.centre_id, Inspection.status, func.count(Inspection.id))
        .group_by(Inspection.centre_id, Inspection.status)
    )
    ins_rows = (await db.execute(ins_stmt)).all()
    completed: dict[str, int] = {}
    totals: dict[str, int] = {}
    for centre_id, status_val, count in ins_rows:
        totals[centre_id] = totals.get(centre_id, 0) + count
        if status_val == "completed":
            completed[centre_id] = count

    scores = []
    for centre in centres:
        total = totals.get(centre.id, 0)
        comp = round((completed.get(centre.id, 0) / total * 100) if total > 0 else 0.0, 1)
        scores.append({
            "centre_id": centre.id,
            "compliance_score": comp,
            "completed_inspections": completed.get(centre.id, 0),
            "total_inspections": total,
        })
    return scores


# ─── Sync Queue Router ───
sync_router = APIRouter(prefix="/sync", tags=["sync"])

# Constants to avoid duplication
SYNC_NOT_FOUND = "Sync item not found"


def _sync_scope(stmt, current: TokenPayload):
    """Non-admins see their own queue items plus legacy ownerless rows
    (enqueued before ownership existed — grandfathered, not orphaned)."""
    if current.role == "admin":
        return stmt
    return stmt.where(
        or_(SyncQueue.owner_id == current.user_id, SyncQueue.owner_id.is_(None))
    )


def _check_sync_owner(current: TokenPayload, item: SyncQueue) -> None:
    """Non-admins may only transition their own (or legacy ownerless) items.
    404 masks existence, matching the notifications convention."""
    if current.role == "admin":
        return
    if item.owner_id is not None and item.owner_id != current.user_id:
        raise HTTPException(status_code=404, detail=SYNC_NOT_FOUND)


class SyncEnqueue(BaseModel):
    entity_type: str
    entity_id: str
    operation: str  # create, update, delete
    payload: dict
    idempotency_key: str


class MarkFailedRequest(BaseModel):
    error: str


@sync_router.post("/enqueue", status_code=status.HTTP_200_OK)
async def enqueue_sync(
    body: SyncEnqueue,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    # Check idempotency
    result = await db.execute(
        select(SyncQueue).where(SyncQueue.idempotency_key == body.idempotency_key)
    )
    existing = result.scalar_one_or_none()
    if existing:
        _check_sync_owner(user, existing)
        return {
            "id": existing.id,
            "entity_type": existing.entity_type,
            "entity_id": existing.entity_id,
            "operation": existing.operation,
            "payload": existing.payload or {},
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
        payload=body.payload,
        idempotency_key=body.idempotency_key,
        owner_id=user.user_id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@sync_router.get("/pending")
async def list_pending_sync(
    entity_type: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    stmt = (
        select(SyncQueue)
        .where(SyncQueue.status == "pending")
        .order_by(SyncQueue.created_at)
        .limit(limit)
    )
    stmt = _sync_scope(stmt, current)
    if entity_type:
        stmt = stmt.where(SyncQueue.entity_type == entity_type)

    result = await db.execute(stmt)
    return result.scalars().all()


@sync_router.post("/mark-synced/{sync_id}", responses={404: {"description": "Sync item not found"}})
async def mark_synced(
    sync_id: str,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.id == sync_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=SYNC_NOT_FOUND)
    _check_sync_owner(current, item)

    item.status = "synced"
    item.synced_at = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    return item


@sync_router.post("/mark-failed/{sync_id}", responses={404: {"description": "Sync item not found"}})
async def mark_failed(
    sync_id: str,
    body: MarkFailedRequest,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.id == sync_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=SYNC_NOT_FOUND)
    _check_sync_owner(current, item)

    item.status = "failed"
    item.error = body.error
    item.retry_count += 1
    await db.commit()
    return item


class RetryFailedRequest(BaseModel):
    max_retries: int = 3


MAX_RETRY_BATCH = 100


@sync_router.post("/retry-failed")
async def retry_failed(
    body: RetryFailedRequest,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    stmt = select(SyncQueue).where(
        SyncQueue.status == "failed", SyncQueue.retry_count < body.max_retries
    )
    result = await db.execute(_sync_scope(stmt, current).limit(MAX_RETRY_BATCH))
    items = result.scalars().all()
    count = 0
    for item in items:
        item.status = "pending"
        item.error = None
        count += 1
    await db.commit()
    return {"retried": count}


@sync_router.get(
    "/status/{idempotency_key}",
    responses={404: {"description": "Sync item not found"}},
)
async def sync_status(
    idempotency_key: str,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.idempotency_key == idempotency_key))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=SYNC_NOT_FOUND)
    _check_sync_owner(current, item)
    return item
