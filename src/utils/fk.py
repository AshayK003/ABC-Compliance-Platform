from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def assert_fk_exists(db: AsyncSession, model, id_value: str | None, name: str) -> None:
    """Raise 400 if a referenced entity does not exist (clearer than a 500 from an FK violation)."""
    if not id_value:
        return
    result = await db.execute(select(model).where(model.id == id_value))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {name}: no such {name} with id '{id_value}'",
        )
