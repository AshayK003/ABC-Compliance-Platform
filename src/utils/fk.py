from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def assert_fk_exists(db: AsyncSession, model, id_value: str | None, name: str) -> Any | None:
    """Raise 400 if a referenced entity does not exist (clearer than a 500 from an FK violation).

    Returns the fetched row so callers can run same-centre linkage checks
    without a second query, or None when the id is None (optional FK) or the
    result is not a real model row (unconfigured test doubles).
    """
    if id_value is None:
        return None
    if not isinstance(id_value, str) or not id_value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {name}: id must be a non-empty string",
        )
    result = await db.execute(select(model).where(model.id == id_value))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {name}: no such {name} with id '{id_value}'",
        )
    return obj if isinstance(obj, model) else None
