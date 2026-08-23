from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.config import settings

# Pool sized for ~100 concurrent admin sessions (issue #15). NullPool for
# tests / debug so each connection is fresh and no pool state leaks between
# test cases.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # drop dead connections (serverless DBs like Neon recycle aggressively)
    **({} if settings.debug else {"pool_size": 20, "max_overflow": 10, "pool_timeout": 30}),
    poolclass=NullPool if settings.debug else None,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
