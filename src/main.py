# ABC Compliance Platform — Digital compliance infrastructure for Animal Birth Control centres
# Copyright (C) 2025 Ashay Kushwaha
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.routes import router as auth_router
from src.centres.routes import router as centres_router
from src.config import settings
from src.database import get_db
from src.dogs.routes import router as dogs_router
from src.funds.routes import alloc_router, exp_router
from src.funds.routes import router as funds_router
from src.inspections.routes import router as inspections_router
from src.notifications.routes import router as notifications_router
from src.public.routes import public_router, sync_router, public_limiter
from src.reports.routes import router as reports_router
from src.surgeries.routes import router as surgeries_router
from src.audit.routes import router as audit_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(centres_router)
api_v1_router.include_router(dogs_router)
api_v1_router.include_router(funds_router)
api_v1_router.include_router(alloc_router)
api_v1_router.include_router(exp_router)
api_v1_router.include_router(inspections_router)
api_v1_router.include_router(public_router)
api_v1_router.include_router(sync_router)
api_v1_router.include_router(surgeries_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(audit_router)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


# Correlation ID middleware
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id
        return response


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting %s v%s", settings.app_name, "0.1.0")
    yield
    # Shutdown
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.state.public_limiter = public_limiter
app.add_middleware(CorrelationIDMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.exception(
        "Unhandled error: %s %s | correlation_id=%s",
        request.method,
        request.url.path,
        correlation_id,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # CSP - restrictive but allows inline styles for dev tools
    if settings.debug:
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    else:
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    response.headers["Content-Security-Policy"] = csp
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

app.include_router(api_v1_router)


@app.get("/health")
async def health(db: Annotated[AsyncSession, Depends(get_db)]):  # noqa: B008
    checks = {
        "database": True,
        "redis": True,  # Redis check optional
    }
    try:
        await db.execute(select(1))
    except Exception as e:
        correlation_id = getattr(db, "state", {}).get("correlation_id", "unknown")
        logger.warning(
            "Health check DB failed: %s | correlation_id=%s", e, correlation_id
        )
        checks["database"] = False

    healthy = all(checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "healthy" if healthy else "degraded", "checks": checks},
    )
