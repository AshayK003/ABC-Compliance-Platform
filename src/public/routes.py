from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Centre, Complaint, Inspection, SyncQueue

# Rate limiter for public endpoints
public_limiter = Limiter(key_func=get_remote_address)

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
@public_limiter.limit("10/hour")
async def create_complaint(
    request: Request,
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


@public_router.get(
    "/complaints/{complaint_id}",
    responses={404: {"description": "Complaint not found"}},
)
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


@public_router.patch(
    "/complaints/{complaint_id}",
    responses={404: {"description": "Complaint not found"}},
)
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


# ─── Sync Queue Router ───
sync_router = APIRouter(prefix="/sync", tags=["sync"])

# Constants to avoid duplication
SYNC_NOT_FOUND = "Sync item not found"


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


@sync_router.post("/mark-synced/{sync_id}", responses={404: {"description": "Sync item not found"}})
async def mark_synced(
    sync_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.id == sync_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=SYNC_NOT_FOUND)

    item.status = "synced"
    # synced_at is set by model default
    await db.commit()
    return item


@sync_router.post("/mark-failed/{sync_id}", responses={404: {"description": "Sync item not found"}})
async def mark_failed(
    sync_id: str,
    body: MarkFailedRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.id == sync_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=SYNC_NOT_FOUND)

    item.status = "failed"
    item.error = body.error
    item.retry_count += 1
    await db.commit()
    return item


class RetryFailedRequest(BaseModel):
    max_retries: int = 3


@sync_router.post("/retry-failed")
async def retry_failed(
    body: RetryFailedRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(
        select(SyncQueue).where(SyncQueue.status == "failed", SyncQueue.retry_count < body.max_retries)
    )
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
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(SyncQueue).where(SyncQueue.idempotency_key == idempotency_key))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=SYNC_NOT_FOUND)
    return item
