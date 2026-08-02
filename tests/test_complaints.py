from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
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
    async def test_creates_and_returns_complaint(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
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


class TestUpdateComplaint:
    @pytest.mark.asyncio
    async def test_updates_status_and_resolution(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        c1 = _make_complaint(id="comp-1", status="open")
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = c1
        mock_session.execute.return_value = mr
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        resp = await client.patch(
            "/public/complaints/comp-1",
            json={"status": "resolved", "resolution": "Centre visited, issue closed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"
        assert resp.json()["resolution"] == "Centre visited, issue closed"
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_404_for_missing(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mr

        resp = await client.patch("/public/complaints/nonexistent", json={"status": "resolved"})
        assert resp.status_code == 404


class TestComplianceHeatmap:
    @pytest.mark.asyncio
    async def test_states_with_no_inspections_still_appear(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        # Two centres, no inspections at all
        centres_mr = MagicMock()
        centres_mr.all.return_value = [
            SimpleNamespace(id="c1", state="Kerala"),
            SimpleNamespace(id="c2", state="Delhi"),
        ]
        ins_mr = MagicMock()
        ins_mr.all.return_value = []
        mock_session.execute = AsyncMock(side_effect=[centres_mr, ins_mr])

        resp = await client.get("/public/heatmap")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        states = {d["state"]: d for d in data}
        assert states["Kerala"]["centres"] == 1
        assert states["Kerala"]["inspections"] == 0
        assert states["Kerala"]["compliance_rate"] == 0.0
        assert states["Kerala"]["risk"] == "critical"

    @pytest.mark.asyncio
    async def test_compliance_rate_and_risk_aggregation(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        # One centre with 2 completed + 1 pending inspection -> 66.7% moderate
        centres_mr = MagicMock()
        centres_mr.all.return_value = [SimpleNamespace(id="c1", state="Kerala")]
        ins_mr = MagicMock()
        ins_mr.all.return_value = [
            ("c1", "completed", 2),
            ("c1", "pending", 1),
        ]
        mock_session.execute = AsyncMock(side_effect=[centres_mr, ins_mr])

        resp = await client.get("/public/heatmap")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        entry = data[0]
        assert entry["centres"] == 1
        assert entry["inspections"] == 3
        assert entry["compliance_rate"] == 66.7
        assert entry["risk"] == "moderate"

    @pytest.mark.asyncio
    async def test_critical_first_sorting(self, client: AsyncClient, mock_session: AsyncMock):
        # Two states: one compliant (80%+), one critical (0%) -> critical sorted first
        centres_mr = MagicMock()
        centres_mr.all.return_value = [
            SimpleNamespace(id="c1", state="Kerala"),
            SimpleNamespace(id="c2", state="Delhi"),
        ]
        ins_mr = MagicMock()
        ins_mr.all.return_value = [
            ("c2", "completed", 5),
            ("c2", "pending", 1),  # 83.3% compliant
        ]
        mock_session.execute = AsyncMock(side_effect=[centres_mr, ins_mr])

        resp = await client.get("/public/heatmap")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["state"] == "Kerala"
        assert data[0]["risk"] == "critical"
        assert data[1]["state"] == "Delhi"
        assert data[1]["risk"] == "compliant"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_centres(self, client: AsyncClient, mock_session: AsyncMock):
        centres_mr = MagicMock()
        centres_mr.all.return_value = []
        mock_session.execute = AsyncMock(return_value=centres_mr)

        resp = await client.get("/public/heatmap")
        assert resp.status_code == 200
        assert resp.json() == []
