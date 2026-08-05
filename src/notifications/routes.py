from __future__ import annotations

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _resolve_user_id(current: TokenPayload, user_id: Optional[str]) -> str:
    """Admins may query another user; everyone else is scoped to themselves."""
    if user_id and current.role == "admin":
        return user_id
    return current.user_id


class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str = "info"  # info, warning, error, success
    read: bool = False


class NotificationUpdate(BaseModel):
    read: Optional[bool] = None
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None


class NotificationOut(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    read: bool
    created_at: datetime


@router.post("", status_code=201)
async def create_notification(
    body: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    notification = Notification(**body.model_dump())
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


@router.get("")
async def list_notifications(
    user_id: Optional[str] = None,
    read: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    effective_user_id = _resolve_user_id(current, user_id)
    stmt = (
        select(Notification)
        .where(Notification.user_id == effective_user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if read is not None:
        stmt = stmt.where(Notification.read == read)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/unread-count")
async def get_unread_count(
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    effective_user_id = _resolve_user_id(current, user_id)
    stmt = (
        select(func.count(Notification.id))
        .where(Notification.read == False)  # noqa: E712
        .where(Notification.user_id == effective_user_id)
    )
    result = await db.execute(stmt)
    return {"count": result.scalar() or 0}


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current.user_id and current.role != "admin":
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.patch("/{notification_id}")
async def update_notification(
    notification_id: str,
    body: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current.user_id and current.role != "admin":
        raise HTTPException(status_code=404, detail="Notification not found")
    
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(notification, key, value)
    
    await db.commit()
    await db.refresh(notification)
    return notification


@router.post("/mark-all-read")
async def mark_all_read(
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current: TokenPayload = Depends(get_current_user),
):
    from src.models.base import Notification

    effective_user_id = _resolve_user_id(current, user_id)
    stmt = (
        select(Notification)
        .where(Notification.read == False)  # noqa: E712
        .where(Notification.user_id == effective_user_id)
    )
    
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    
    count = 0
    for notification in notifications:
        notification.read = True
        count += 1
    
    await db.commit()
    return {"updated": count}