from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import (
    TokenPayload,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from src.database import get_db
from src.models.base import Staff

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    phone: str
    password: str
    role: str = "vet"
    centre_id: str | None = None


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Staff).where(Staff.phone == body.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

    staff = Staff(
        name=body.name,
        phone=body.phone,
        role=body.role,
        centre_id=body.centre_id or "",
        password_hash=hash_password(body.password),
    )
    db.add(staff)
    await db.commit()
    return {"id": staff.id, "name": staff.name, "role": staff.role}


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Staff).where(Staff.phone == body.phone))
    staff = result.scalar_one_or_none()
    if not staff or not verify_password(body.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user_id=staff.id, role=staff.role)
    return TokenResponse(access_token=token, user_id=staff.id, role=staff.role)


@router.get("/me")
async def me(user: TokenPayload = Depends(get_current_user)):
    return user
