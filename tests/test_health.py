from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock

from src.database import get_db
from src.main import app


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=AsyncMock(scalar=MagicMock(return_value=1)))
    return db


@pytest.fixture
def app_with_db(mock_db):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_db):
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["checks"]["database"] is True
