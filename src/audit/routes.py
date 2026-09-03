from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, require_role
from src.database import get_db
from src.models.base import AuditEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventCreate(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    details: dict | None = None


class AuditEventOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    timestamp: datetime
    details: dict | None = None


class AuditEventList(BaseModel):
    data: list
    total: int
    page: int
    page_size: int


async def log_audit_event(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: str,
    details: dict | None = None,
) -> AuditEvent:
    """Log an audit event to the database.

    Best-effort by design: auditing must never fail the user operation it
    records (a 500-after-create makes clients retry into duplicates). A
    lost event is logged server-side with full context instead.
    """
    audit_event = AuditEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        timestamp=datetime.now(UTC).replace(tzinfo=None),
        details=details,
    )
    db.add(audit_event)
    try:
        await db.commit()
        await db.refresh(audit_event)
    except Exception:
        await db.rollback()
        logger.exception(
            "audit event dropped: %s %s actor=%s", entity_type, action, actor_id
        )
    return audit_event


@router.post("", response_model=AuditEventOut, status_code=201)
async def create_audit_event(
    body: AuditEventCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role("admin")),
):
    """Admin-only manual audit entry. All routine events are written
    server-side via log_audit_event; this endpoint exists for exceptional
    backfills, never for regular clients (prevents trail forgery)."""
    audit_event = AuditEvent(
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        action=body.action,
        actor_id=user.user_id,
        details=body.details,
    )
    db.add(audit_event)
    await db.commit()
    await db.refresh(audit_event)
    return audit_event


@router.get("", response_model=list[AuditEventOut])
async def list_audit_events(
    entity_type: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    actor_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    stmt = select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit).offset(offset)

    if entity_type:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditEvent.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditEvent.action == action)
    if actor_id:
        stmt = stmt.where(AuditEvent.actor_id == actor_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/stats")
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    """Get audit statistics."""
    total_events = await db.execute(select(func.count(AuditEvent.id)))
    total = total_events.scalar() or 0

    # Actions breakdown
    actions_stmt = select(AuditEvent.action, func.count(AuditEvent.id)).group_by(AuditEvent.action)
    actions_result = await db.execute(actions_stmt)
    actions = {row[0]: row[1] for row in actions_result.all()}

    # Entity types breakdown
    entities_stmt = select(AuditEvent.entity_type, func.count(AuditEvent.id)).group_by(
        AuditEvent.entity_type
    )
    entities_result = await db.execute(entities_stmt)
    entities = {row[0]: row[1] for row in entities_result.all()}

    # Top actors
    actors_stmt = (
        select(AuditEvent.actor_id, func.count(AuditEvent.id))
        .group_by(AuditEvent.actor_id)
        .order_by(func.count(AuditEvent.id).desc())
        .limit(10)
    )
    actors_result = await db.execute(actors_stmt)
    top_actors = [{"actor_id": row[0], "count": row[1]} for row in actors_result.all()]

    return {
        "total_events": total,
        "actions": actions,
        "entity_types": entities,
        "top_actors": top_actors,
    }
