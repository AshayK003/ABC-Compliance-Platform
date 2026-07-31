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
from src.models.base import Complaint


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


def _make_complaint(**kwargs) -> Complaint:
    data = {
        "id": "comp-1",
        "centre_id": "centre-1",
        "citizen_phone": "9876543210",
        "description": "Test complaint",
        "status": "open",
        "sla_deadline": None,
        "resolution": None,
        "created_at": datetime(2026, 7, 30, 10, 0, 0),
    }
    data.update(kwargs)
    return Complaint(**data)


class TestCreateComplaint:
    @pytest.mark.asyncio
    async def test_creates_and_returns_complaint(self, client: AsyncClient, mock_session: AsyncMock):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        resp = await client.post("/public/complaints", json={
            "centre_id": "centre-1",
            "citizen_phone": "9876543210",
            "description": "Test complaint",
        })
        assert resp.status_code == 201
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_requires_centre_phone_desc(self, client: AsyncClient):
        resp = await client.post("/public/complaints", json={})
        assert resp.status_code == 422


class TestListComplaints:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/public/complaints")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_complaints(self, client: AsyncClient, mock_session: AsyncMock):
        c1 = _make_complaint(id="c1", centre_id="centre-1")
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [c1]
        mock_session.execute.return_value = mr

        resp = await client.get("/public/complaints")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["centre_id"] == "centre-1"

    @pytest.mark.asyncio
    async def test_filters_by_centre_id(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/public/complaints?centre_id=centre-1")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_filters_by_status(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/public/complaints?status=open")
        assert resp.status_code == 200


class TestGetComplaint:
    @pytest.mark.asyncio
    async def test_returns_complaint_by_id(self, client: AsyncClient, mock_session: AsyncMock):
        c1 = _make_complaint(id="comp-1")
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = c1
        mock_session.execute.return_value = mr

        resp = await client.get("/public/complaints/comp-1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "comp-1"

    @pytest.mark.asyncio
    async def test_404_for_missing(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mr

        resp = await client.get("/public/complaints/nonexistent")
        assert resp.status_code == 404