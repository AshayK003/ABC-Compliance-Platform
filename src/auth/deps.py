from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.base import Staff

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(
    user_id: str,
    role: str,
    name: str | None = None,
    phone: str | None = None,
    centre_id: str | None = None,
) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "name": name,
        "phone": phone,
        "centre_id": centre_id,
        "type": "access",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: str, token_version: int = 0) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "tv": token_version,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None


class TokenPayload(BaseModel):
    user_id: str
    role: str
    name: str | None = None
    phone: str | None = None
    centre_id: str | None = None


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),  # noqa: B008
) -> TokenPayload:
    # Accept either an Authorization: Bearer header or the httpOnly access
    # token cookie. Cookie fallback keeps cookie-only flows (file downloads,
    # server-side redirects) authenticated without exposing the token to JS.
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return TokenPayload(
        user_id=payload["sub"],
        role=payload["role"],
        name=payload.get("name"),
        phone=payload.get("phone"),
        centre_id=payload.get("centre_id"),
    )


async def verify_refresh_token(refresh_token: str, db: AsyncSession) -> TokenPayload:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload["sub"]
    token_version = payload.get("tv", 0)
    result = await db.execute(select(Staff).where(Staff.id == user_id))
    staff = result.scalar_one_or_none()
    if not staff or not staff.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    # Revoked: the user logged out (or changed password), invalidating all
    # previously issued refresh tokens. Access tokens still expire on their own.
    if staff.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked — please log in again",
        )
    return TokenPayload(
        user_id=staff.id,
        role=staff.role,
        name=staff.name,
        phone=staff.phone,
        centre_id=staff.centre_id,
    )


def _cookie_samesite() -> Literal["strict", "none"]:
    # Local dev (same-site localhost): Strict is fine and maximally CSRF-safe.
    # Production splits frontend/backend across sites (e.g. vercel.app ↔
    # hf.space); Strict cookies never attach to cross-site requests, so use
    # None (+ Secure) there. JSON-only bodies + restricted CORS keep CSRF
    # exposure low.
    return "strict" if settings.debug else "none"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # secure=False in debug so cookies work over plain-http localhost;
    # browsers treat localhost as trustworthy, prod always gets Secure.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.debug,
        samesite=_cookie_samesite(),
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite=_cookie_samesite(),
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", secure=not settings.debug, samesite=_cookie_samesite())
    response.delete_cookie("refresh_token", secure=not settings.debug, samesite=_cookie_samesite())


def require_centre_access(centre_id_param: str = "centre_id"):
    """Object-level authorization for entity routers (anti-IDOR).

    Returns a dependency factory: admins pass; everyone else may only touch
    entities whose centre_id matches their own staff.centre_id. Staff without
    a centre assignment are read-blocked from all centres.

    The centre id is read from the query/path params first, then from the
    JSON body (POST/PUT/PATCH create routes carry it in the body, where a
    plain ``centre_id: str | None`` parameter would never bind). Reading the
    body here is safe: Starlette caches ``request.body()`` for the handler.

    Usage on a route with a `centre_id` path/query/body param:
        _: TokenPayload = Depends(require_centre_access("centre_id"))
    """

    async def _check(
        request: Request = None,  # type: ignore[assignment]  # injected by FastAPI; None in direct unit calls
        centre_id: str | None = None,
        current: TokenPayload = Depends(get_current_user),  # noqa: B008
    ) -> TokenPayload:
        if current.role == "admin":
            return current
        if centre_id is None and request is not None and request.method in ("POST", "PUT", "PATCH"):
            try:
                payload = await request.json()
            except Exception:
                payload = None
            if isinstance(payload, dict):
                value = payload.get(centre_id_param)
                centre_id = value if isinstance(value, str) and value else None
        if not centre_id or centre_id != current.centre_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: resource belongs to another centre",
            )
        return current

    _check.__name__ = f"require_centre_access[{centre_id_param}]"
    return _check


def check_centre_read(current: TokenPayload, centre_id: str | None) -> None:
    """Object-level read guard: non-admins may only read their own centre's
    records. Raises 404 (not 403) so record existence isn't leaked to
    cross-centre callers."""
    if current.role == "admin":
        return
    if not centre_id or centre_id != current.centre_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def scope_centre_filter(current: TokenPayload, centre_id: str | None) -> str | None:
    """Force list-endpoint filters to the caller's centre for non-admins.

    Admins keep the requested filter. Non-admins requesting another centre
    get 403; non-admins with no filter (or a matching one) are scoped to
    their own centre. Staff without a centre assignment are blocked."""
    if current.role == "admin":
        return centre_id
    if not current.centre_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: no centre assigned to this account",
        )
    if centre_id is not None and centre_id != current.centre_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: resource belongs to another centre",
        )
    return current.centre_id


def require_role(*roles: str):
    def checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:  # noqa: B008
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user
    return checker
