from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Dog

router = APIRouter(prefix="/dogs", tags=["dogs"])


class DogCreate(BaseModel):
    centre_id: str
    tag_id: str
    sex: str
    age_estimate: int | None = None
    weight: float | None = None
    status: str = "registered"


@router.post("", status_code=201)
async def create_dog(
    body: DogCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    dog = Dog(**body.model_dump())
    db.add(dog)
    await db.commit()
    await db.refresh(dog)
    return dog


@router.get("")
async def list_dogs(
    centre_id: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    stmt = select(Dog).order_by(Dog.tag_id)
    if centre_id:
        stmt = stmt.where(Dog.centre_id == centre_id)
    if status:
        stmt = stmt.where(Dog.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{dog_id}", responses={404: {"description": "Dog not found"}})
async def get_dog(
    dog_id: str,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    result = await db.execute(select(Dog).where(Dog.id == dog_id))
    dog = result.scalar_one_or_none()
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    return dog
