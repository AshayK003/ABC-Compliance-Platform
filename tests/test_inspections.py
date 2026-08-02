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
from src.models.base import Inspection


@pytest.fixture
def app() -> FastAPI:
    _app.dependency_overrides.clear()
    return _app


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    return session


@pytest.fixture
def auth_override():
    def _override():
        return TokenPayload(user_id="test-user-id", role="admin")
    return _override


@pytest.fixture
async def client(app: FastAPI, mock_session: AsyncMock, auth_override) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_user] = auth_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_inspection(**kwargs) -> Inspection:
    data = {
        "id": "insp-1",
        "centre_id": "centre-1",
        "inspector_id": "staff-1",
        "scheduled_at": datetime(2026, 7, 30, 10, 0, 0),
        "conducted_at": None,
        "status": "scheduled",
        "findings": None,
        "signoff_hash": None,
    }
    data.update(kwargs)
    return Inspection(**data)


class TestCreateInspection:
    @pytest.mark.asyncio
    async def test_creates_and_returns_inspection(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        resp = await client.post("/api/v1/inspections", json={
            "centre_id": "centre-1",
            "inspector_id": "staff-1",
            "scheduled_at": "2026-07-30T10:00:00",
        })
        assert resp.status_code == 201
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_requires_centre_and_inspector(self, client: AsyncClient):
        resp = await client.post("/api/v1/inspections", json={})
        assert resp.status_code == 422


class TestListInspections:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/inspections")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_inspections(self, client: AsyncClient, mock_session: AsyncMock):
        i1 = _make_inspection(id="i1", centre_id="centre-1")
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [i1]
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/inspections")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["centre_id"] == "centre-1"

    @pytest.mark.asyncio
    async def test_filters_by_centre_id(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/inspections?centre_id=centre-1")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_filters_by_status(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/inspections?status=scheduled")
        assert resp.status_code == 200


class TestGetInspection:
    @pytest.mark.asyncio
    async def test_returns_inspection_by_id(self, client: AsyncClient, mock_session: AsyncMock):
        i1 = _make_inspection(id="insp-1")
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = i1
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/inspections/insp-1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "insp-1"

    @pytest.mark.asyncio
    async def test_404_for_missing(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/inspections/nonexistent")
        assert resp.status_code == 404
