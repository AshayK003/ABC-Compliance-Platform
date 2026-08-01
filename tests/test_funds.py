from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user
from src.database import get_db
from src.main import app as _app
from src.models.base import Allocation, Expense, Grant


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


def _make_grant(**kwargs) -> Grant:
    data = {
        "id": "grant-1",
        "awbi_ref": "AWBI/2026/001",
        "amount": 1000000.0,
        "purpose": "ABC Programme",
        "financial_year": "2026-27",
        "status": "active",
    }
    data.update(kwargs)
    return Grant(**data)


def _make_allocation(**kwargs) -> Allocation:
    data = {
        "id": "alloc-1",
        "grant_id": "grant-1",
        "centre_id": "centre-1",
        "amount": 500000.0,
        "allocated_at": datetime(2026, 7, 30, 10, 0, 0),
    }
    data.update(kwargs)
    return Allocation(**data)


def _make_expense(**kwargs) -> Expense:
    data = {
        "id": "exp-1",
        "allocation_id": "alloc-1",
        "surgery_id": None,
        "category": "medicine",
        "amount": 25000.0,
        "bill_ref": "BILL-001",
        "expense_at": datetime(2026, 7, 30).date(),
    }
    data.update(kwargs)
    return Expense(**data)


class TestGrantCRUD:
    @pytest.mark.asyncio
    async def test_create_grant(self, client: AsyncClient, mock_session: AsyncMock):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        resp = await client.post("/grants", json={
            "awbi_ref": "AWBI/2026/001",
            "amount": 1000000.0,
            "purpose": "ABC Programme",
            "financial_year": "2026-27",
        })
        assert resp.status_code == 201
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_grants(self, client: AsyncClient, mock_session: AsyncMock):
        g1 = _make_grant(id="g1")
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [g1]
        mock_session.execute.return_value = mr

        resp = await client.get("/grants")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestAllocationCRUD:
    @pytest.mark.asyncio
    async def test_create_allocation(self, client: AsyncClient, mock_session: AsyncMock):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        resp = await client.post("/allocations", json={
            "grant_id": "grant-1",
            "centre_id": "centre-1",
            "amount": 500000.0,
        })
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_list_allocations(self, client: AsyncClient, mock_session: AsyncMock):
        a1 = _make_allocation(id="a1")
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [a1]
        mock_session.execute.return_value = mr

        resp = await client.get("/allocations")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_filter_by_grant_id(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/allocations?grant_id=grant-1")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_centre_id(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/allocations?centre_id=centre-1")
        assert resp.status_code == 200


class TestExpenseCRUD:
    @pytest.mark.asyncio
    async def test_create_expense(self, client: AsyncClient, mock_session: AsyncMock):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock allocation lookup
        alloc = _make_allocation(id="alloc-1", amount=Decimal("100000.0"))
        mr_alloc = MagicMock()
        mr_alloc.scalar_one_or_none.return_value = alloc

        # Mock sum query
        mr_sum = MagicMock()
        mr_sum.scalar.return_value = Decimal("0")

        # Return different mocks for the two queries
        mock_session.execute.side_effect = [mr_alloc, mr_sum]

        resp = await client.post("/expenses", json={
            "allocation_id": "alloc-1",
            "category": "medicine",
            "amount": 25000.0,
            "bill_ref": "BILL-001",
        })
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_list_expenses(self, client: AsyncClient, mock_session: AsyncMock):
        e1 = _make_expense(id="e1")
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [e1]
        mock_session.execute.return_value = mr

        resp = await client.get("/expenses")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_filter_by_allocation_id(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/expenses?allocation_id=alloc-1")
        assert resp.status_code == 200
