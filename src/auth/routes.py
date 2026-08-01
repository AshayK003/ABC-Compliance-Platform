from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import (
    TokenPayload,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    set_auth_cookies,
    verify_password,
    verify_refresh_token,
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


class RegisterResponse(BaseModel):
    id: str
    name: str
    role: str
    access_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Staff).where(Staff.phone == body.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

    staff = Staff(
        name=body.name,
        phone=body.phone,
        role=body.role,
        centre_id=(body.centre_id or None),
        password_hash=hash_password(body.password),
    )
    db.add(staff)
    await db.commit()

    access_token = create_access_token(user_id=staff.id, role=staff.role)
    refresh_token = create_refresh_token(user_id=staff.id)
    set_auth_cookies(response, access_token, refresh_token)

    return RegisterResponse(
        id=staff.id, name=staff.name, role=staff.role, access_token=access_token
    )


@router.post("/login")
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Staff).where(Staff.phone == body.phone))
    staff = result.scalar_one_or_none()
    if not staff or not verify_password(body.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(user_id=staff.id, role=staff.role)
    refresh_token = create_refresh_token(user_id=staff.id)
    set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(access_token=access_token, user_id=staff.id, role=staff.role)


@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    user = await verify_refresh_token(refresh_token, db)

    access_token = create_access_token(user_id=user.user_id, role=user.role)
    new_refresh_token = create_refresh_token(user_id=user.user_id)
    set_auth_cookies(response, access_token, new_refresh_token)

    return TokenResponse(access_token=access_token, user_id=user.user_id, role=user.role)


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.delete("/me")
async def delete_account(user: TokenPayload = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Staff).where(Staff.id == user.user_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(staff)
    await db.commit()
    
    response = Response(content='{"message": "Account deleted"}', media_type="application/json")
    clear_auth_cookies(response)
    return response


@router.get("/me")
async def me(user: TokenPayload = Depends(get_current_user)):
    return user
