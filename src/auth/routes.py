from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import (
    TokenPayload,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    require_role,
    set_auth_cookies,
    verify_password,
    verify_refresh_token,
)
from src.cache import invalidate_pattern
from src.database import get_db
from src.models.base import Centre, Staff
from src.ratelimit import limiter
from src.utils.fk import assert_fk_exists

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=128)
    centre_id: str | None = None


class LoginRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class RegisterResponse(BaseModel):
    id: str
    name: str
    status: str = "pending_approval"
    message: str


class UserAdminUpdate(BaseModel):
    active: bool | None = None
    role: str | None = None
    centre_id: str | None = None


class StaffOut(BaseModel):
    """Admin-facing staff view — never includes password_hash/token_version."""

    id: str
    centre_id: str | None
    name: str
    role: str
    phone: str
    active: bool


@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"description": "Phone already registered"}},
)
@limiter.limit("3/hour")
async def register(
    request: Request,
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Self-registration creates an INACTIVE staff record pending admin
    approval. No session is issued; role and centre assignment happen only
    through the admin user-management endpoints."""
    result = await db.execute(select(Staff).where(Staff.phone == body.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

    if body.centre_id:
        await assert_fk_exists(db, Centre, body.centre_id, "centre")

    staff = Staff(
        name=body.name,
        phone=body.phone,
        role="vet",
        centre_id=(body.centre_id or None),
        password_hash=hash_password(body.password),
        active=False,  # pending admin approval
    )
    db.add(staff)
    try:
        await db.commit()
        await db.refresh(staff)
    except Exception as e:
        await db.rollback()
        if "phone" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone already registered",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        ) from e

    # New staff row affects centres-list staff counts.
    invalidate_pattern("centres:")
    return RegisterResponse(
        id=staff.id,
        name=staff.name,
        message="Registration received. An administrator will review and activate your account.",
    )


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Staff).where(Staff.phone == body.phone))
    staff = result.scalar_one_or_none()
    if not staff or not verify_password(body.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not staff.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    access_token = create_access_token(
        user_id=staff.id,
        role=staff.role,
        name=staff.name,
        phone=staff.phone,
        centre_id=staff.centre_id,
    )
    refresh_token = create_refresh_token(user_id=staff.id, token_version=staff.token_version)
    set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(access_token=access_token, user_id=staff.id, role=staff.role)


@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    user = await verify_refresh_token(refresh_token, db)

    access_token = create_access_token(
        user_id=user.user_id,
        role=user.role,
        name=user.name,
        phone=user.phone,
        centre_id=user.centre_id,
    )
    # Issue new refresh token with current token_version
    result = await db.execute(select(Staff).where(Staff.id == user.user_id))
    staff = result.scalar_one_or_none()
    new_refresh_token = create_refresh_token(user_id=user.user_id, token_version=staff.token_version if staff else 0)
    set_auth_cookies(response, access_token, new_refresh_token)

    return TokenResponse(access_token=access_token, user_id=user.user_id, role=user.role)


@router.post("/logout")
async def logout(
    response: Response,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Invalidate all existing refresh tokens by bumping token_version
    result = await db.execute(select(Staff).where(Staff.id == user.user_id))
    staff = result.scalar_one_or_none()
    if staff:
        staff.token_version += 1
        await db.commit()
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.delete("/me", responses={404: {"description": "User not found"}})
async def delete_account(
    response: Response,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate the account instead of hard-deleting.

    Hard-deleting a Staff row breaks the surgical/audit history that references
    it and violates the audit-trail guarantee. Deactivation preserves the
    record, blocks login, and revokes all refresh tokens immediately.
    """
    result = await db.execute(select(Staff).where(Staff.id == user.user_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="User not found")

    staff.active = False
    staff.token_version += 1
    await db.commit()

    clear_auth_cookies(response)
    return {"message": "Account deactivated"}


@router.get("/staff", response_model=list[StaffOut], responses={403: {"description": "Admin only"}})
async def list_staff(
    active: bool | None = None,
    centre_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    """Admin: list staff accounts, optionally filtered by state or centre."""
    stmt = select(Staff).order_by(Staff.name)
    if active is not None:
        stmt = stmt.where(Staff.active == active)
    if centre_id:
        stmt = stmt.where(Staff.centre_id == centre_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/staff/{staff_id}", response_model=StaffOut, responses={404: {"description": "User not found"}})
async def update_staff(
    staff_id: str,
    body: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    """Admin: activate/deactivate an account, change role, or assign centre.

    Activating a pending registration is the approval step for self-signup.
    Deactivating (or reassigning) a user bumps token_version so their existing
    sessions are revoked immediately.
    """
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="User not found")

    if body.centre_id is not None:
        await assert_fk_exists(db, Centre, body.centre_id, "centre")
    if body.role is not None:
        if body.role not in ("vet", "surgeon", "admin"):
            raise HTTPException(status_code=422, detail="Invalid role")
        if staff.role == "admin" and body.role != "admin":
            other_admins = await db.execute(
                select(func.count(Staff.id)).where(Staff.role == "admin", Staff.active == True)  # noqa: E712
            )
            if (other_admins.scalar() or 0) <= 1:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot demote the last active admin",
                )
    if body.active is False and staff.role == "admin":
        other_admins = await db.execute(
            select(func.count(Staff.id)).where(Staff.role == "admin", Staff.active == True)  # noqa: E712
        )
        if (other_admins.scalar() or 0) <= 1:
            raise HTTPException(
                status_code=409,
                detail="Cannot deactivate the last active admin",
            )

    changed = False
    if body.active is not None and body.active != staff.active:
        staff.active = body.active
        changed = True
    if body.role is not None and body.role != staff.role:
        staff.role = body.role
        changed = True
    if body.centre_id is not None and body.centre_id != staff.centre_id:
        staff.centre_id = body.centre_id
        changed = True
    if changed:
        # Role/centre changes must reach the access token; active changes must
        # kill refresh tokens. Bump on any change — cheap and always safe.
        staff.token_version += 1
    await db.commit()
    await db.refresh(staff)
    # Staff membership changed: the centres list embeds staff counts.
    invalidate_pattern("centres:")
    return staff


@router.get("/staff/pending", response_model=list[StaffOut], responses={403: {"description": "Admin only"}})
async def list_pending_staff(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin")),
):
    """Admin: registrations awaiting approval."""
    result = await db.execute(
        select(Staff).where(Staff.active == False).order_by(Staff.name)  # noqa: E712
    )
    return result.scalars().all()


@router.get("/me")
async def me(user: TokenPayload = Depends(get_current_user)):
    return user
