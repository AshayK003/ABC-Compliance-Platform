from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user
from src.database import get_db
from src.main import app as _app
from src.models.base import Centre, Staff


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


def _make_centre(**kwargs) -> Centre:
    data = {
        "id": "centre-1",
        "name": "Lucknow ABC Centre",
        "code": "LKO-01",
        "district": "Lucknow",
        "state": "Uttar Pradesh",
        "capacity": 50,
        "status": "active",
        "staff": [],
    }
    data.update(kwargs)
    return Centre(**data)


def _make_staff(**kwargs) -> Staff:
    data = {
        "id": "staff-1",
        "centre_id": "centre-1",
        "name": "Dr. Test",
        "role": "vet",
        "phone": "9876543210",
        "password_hash": "hash",
        "active": True,
    }
    data.update(kwargs)
    return Staff(**data)


class TestListCentres:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, client: AsyncClient, mock_session: AsyncMock):
        # Mock for count query (returns total=0)
        count_mr = MagicMock()
        count_mr.scalar.return_value = 0
        
        # Mock for main query (returns empty list)
        data_mr = MagicMock()
        data_mr.scalars.return_value.all.return_value = []
        
        # Use side_effect to return different mocks for each call
        mock_session.execute.side_effect = [count_mr, data_mr]

        resp = await client.get("/api/v1/centres")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_returns_centres_with_staff_count(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        c1 = _make_centre(id="c1", staff=[_make_staff(id="s1"), _make_staff(id="s2")])
        mr = MagicMock()
        # New query returns tuples (Centre, staff_count)
        mr.all.return_value = [(c1, 2)]
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/centres")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["code"] == "LKO-01"
        assert data["data"][0]["staff_count"] == 2


class TestCreateCentre:
    @pytest.mark.asyncio
    async def test_creates_centre(self, client: AsyncClient, mock_session: AsyncMock):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        resp = await client.post("/api/v1/centres", json={
            "name": "New Centre",
            "code": "NCR-02",
            "district": "Noida",
            "state": "Uttar Pradesh",
            "capacity": 30,
        })
        assert resp.status_code == 201
        assert resp.json()["code"] == "NCR-02"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_non_admin(self, client: AsyncClient, app: FastAPI):
        def _vet():
            return TokenPayload(user_id="vet-1", role="vet")
        app.dependency_overrides[get_current_user] = _vet

        resp = await client.post("/api/v1/centres", json={
            "name": "New Centre",
            "code": "NCR-02",
            "district": "Noida",
            "state": "Uttar Pradesh",
        })
        assert resp.status_code == 403


class TestGetCentre:
    @pytest.mark.asyncio
    async def test_returns_centre_by_id(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = _make_centre()
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/centres/centre-1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "centre-1"

    @pytest.mark.asyncio
    async def test_404_for_missing(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/centres/nonexistent")
        assert resp.status_code == 404


class TestListCentreStaff:
    @pytest.mark.asyncio
    async def test_returns_staff(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [_make_staff()]
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/centres/centre-1/staff")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["role"] == "vet"

    @pytest.mark.asyncio
    async def test_returns_empty_staff(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/centres/centre-1/staff")
        assert resp.status_code == 200
        assert resp.json() == []
