from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user
from src.database import get_db
from src.main import app as _app
from src.models.base import Surgery


@pytest.fixture
def app() -> FastAPI:
    """Return the app with overridden dependencies for testing."""
    _app.dependency_overrides.clear()
    return _app


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    # session.add() is synchronous in SQLAlchemy
    session.add = MagicMock()
    return session


@pytest.fixture
def auth_override():
    def _override():
        return TokenPayload(user_id="test-user-id", role="admin")
    return _override


@pytest.fixture
async def client(
    app: FastAPI,
    mock_session: AsyncMock,
    auth_override,
) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_user] = auth_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_surgery(**kwargs) -> Surgery:
    """Build a real Surgery model instance for test assertions."""
    data = {
        "dog_id": "dog-1",
        "centre_id": "centre-1",
        "staff_id": "staff-1",
        "surgery_type": "spay",
        "weight": 15.5,
        "complications": None,
        "timestamp": datetime(2026, 7, 30, 10, 0, 0),
        "synced_at": None,
        "audit_hash": None,
    }
    data.update(kwargs)
    return Surgery(**data)


class TestCreateSurgery:
    @pytest.mark.asyncio
    async def test_creates_and_returns_surgery(self, client: AsyncClient, mock_session: AsyncMock):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        payload = {
            "dog_id": "dog-1",
            "centre_id": "centre-1",
            "staff_id": "staff-1",
            "surgery_type": "spay",
            "weight": 15.5,
        }

        resp = await client.post("/api/v1/surgeries", json=payload)

        assert resp.status_code == 201
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_requires_surgery_type(self, client: AsyncClient):
        resp = await client.post("/api/v1/surgeries", json={"dog_id": "dog-1"})
        assert resp.status_code == 422


class TestListSurgeries:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, client: AsyncClient, mock_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/surgeries")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_surgeries(self, client: AsyncClient, mock_session: AsyncMock):
        s1 = _make_surgery(id="s1", surgery_type="spay")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [s1]
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/surgeries")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["surgery_type"] == "spay"

    @pytest.mark.asyncio
    async def test_filters_by_centre_id(self, client: AsyncClient, mock_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/surgeries?centre_id=centre-1")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_filters_by_dog_id(self, client: AsyncClient, mock_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/surgeries?dog_id=dog-1")
        assert resp.status_code == 200


class TestGetSurgery:
    @pytest.mark.asyncio
    async def test_returns_surgery_by_id(self, client: AsyncClient, mock_session: AsyncMock):
        s1 = _make_surgery(id="surg-1", surgery_type="spay")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = s1
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/surgeries/surg-1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "surg-1"

    @pytest.mark.asyncio
    async def test_404_for_missing(self, client: AsyncClient, mock_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/surgeries/nonexistent")
        assert resp.status_code == 404
