"""Committee governance read endpoints backing the Committee Portal."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user
from src.database import get_db
from src.models.base import (
    Committee,
    CommitteeDocument,
    CommitteeMember,
    Decision,
    Meeting,
    Staff,
    Vote,
)

router = APIRouter(prefix="/committee", tags=["committee"])


@router.get("/decisions")
async def list_decisions(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    """Recent decisions with their vote tallies (passed - rejected - abstained)."""
    decisions = (
        await db.execute(
            select(Decision).order_by(Decision.created_at.desc()).limit(limit)
        )
    ).scalars().all()

    tallies: dict[str, dict[str, int]] = {}
    if decisions:
        rows = await db.execute(
            select(Vote.decision_id, Vote.vote)
            .where(Vote.decision_id.in_([d.id for d in decisions]))
        )
        for decision_id, vote_val in rows.all():
            t = tallies.setdefault(decision_id, {"yes": 0, "no": 0, "abstain": 0})
            if vote_val in t:
                t[vote_val] += 1

    return [
        {
            "id": d.id,
            "resolution_id": d.resolution_id,
            "subject": d.subject,
            "status": d.status,
            "decided_at": d.decided_at,
            "tally": tallies.get(d.id, {"yes": 0, "no": 0, "abstain": 0}),
        }
        for d in decisions
    ]


@router.get("/meetings")
async def list_meetings(
    upcoming_only: bool = Query(True),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    stmt = select(Meeting).order_by(Meeting.scheduled_at)
    if upcoming_only:
        stmt = stmt.where(
            Meeting.scheduled_at >= datetime.now(),
            Meeting.status == "scheduled",
        )
    else:
        stmt = stmt.order_by(Meeting.scheduled_at.desc())
    meetings = (await db.execute(stmt.limit(limit))).scalars().all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "scheduled_at": m.scheduled_at,
            "duration_minutes": m.duration_minutes,
            "location": m.location,
            "meeting_type": m.meeting_type,
            "status": m.status,
        }
        for m in meetings
    ]


@router.get("/documents")
async def list_documents(
    limit: int = Query(8, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    docs = (
        await db.execute(
            select(CommitteeDocument)
            .order_by(CommitteeDocument.uploaded_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "uploaded_at": doc.uploaded_at,
        }
        for doc in docs
    ]


@router.get("/members")
async def list_members(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    """Directory of committee members with their staff identity and role."""
    rows = await db.execute(
        select(CommitteeMember, Staff.name, Staff.phone)
        .join(Staff, CommitteeMember.member_id == Staff.id)
        .order_by(CommitteeMember.joined_at)
    )
    members: list[dict[str, Any]] = []
    for member, name, phone in rows.all():
        members.append(
            {
                "id": member.id,
                "name": name,
                "phone": phone,
                "role": member.role,
                "joined_at": member.joined_at,
            }
        )
    return members


@router.get("/overview")
async def committee_overview(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    """First committee record (single-committee deployments)."""
    committee = (
        await db.execute(select(Committee).order_by(Committee.created_at).limit(1))
    ).scalars().first()
    if not committee:
        return None
    return {
        "id": committee.id,
        "name": committee.name,
        "description": committee.description,
    }
