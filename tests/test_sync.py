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
from src.models.base import SyncQueue


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


def _make_sync_queue(**kwargs) -> SyncQueue:
    data = {
        "id": "sync-1",
        "entity_type": "surgery",
        "entity_id": "surg-1",
        "operation": "create",
        "payload": '{"surgery_type": "spay", "dog_id": "dog-1"}',
        "idempotency_key": "idem-123",
        "status": "pending",
        "retry_count": 0,
        "created_at": datetime(2026, 7, 30, 10, 0, 0),
        "synced_at": None,
        "error": None,
    }
    data.update(kwargs)
    return SyncQueue(**data)


def _setup_sync_lookup(mock_session: AsyncMock, item: SyncQueue) -> None:
    """Point the mocked session's execute at a single sync-queue row."""
    mr = MagicMock()
    mr.scalar_one_or_none.return_value = item
    mock_session.execute.return_value = mr


class TestSyncQueue:
    @pytest.mark.asyncio
    async def test_enqueue_operation(self, client: AsyncClient, mock_session: AsyncMock):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mr

        resp = await client.post("/api/v1/sync/enqueue", json={
            "entity_type": "surgery",
            "entity_id": "surg-1",
            "operation": "create",
            "payload": {"surgery_type": "spay", "dog_id": "dog-1"},
            "idempotency_key": "idem-123",
        })
        assert resp.status_code == 200
        assert resp.json()["idempotency_key"] == "idem-123"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_enqueue_duplicate_idempotency_key(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        # First enqueue
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.execute = AsyncMock()
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = _make_sync_queue(idempotency_key="idem-dup")
        mock_session.execute.return_value = mr

        resp = await client.post("/api/v1/sync/enqueue", json={
            "entity_type": "surgery",
            "entity_id": "surg-1",
            "operation": "create",
            "payload": {"surgery_type": "spay"},
            "idempotency_key": "idem-dup",
        })
        assert resp.status_code == 200
        assert resp.json()["idempotency_key"] == "idem-dup"

    @pytest.mark.asyncio
    async def test_list_pending(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [
            _make_sync_queue(id="sync-1", idempotency_key="k1"),
            _make_sync_queue(id="sync-2", idempotency_key="k2", status="pending"),
        ]
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/sync/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_mark_synced(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = _make_sync_queue(id="sync-1", status="pending")
        mock_session.execute.return_value = mr
        mock_session.commit = AsyncMock()

        resp = await client.post("/api/v1/sync/mark-synced/sync-1")
        assert resp.status_code == 200
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mark_failed(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = _make_sync_queue(id="sync-fail", status="pending")
        mock_session.execute.return_value = mr
        mock_session.commit = AsyncMock()

        resp = await client.post("/api/v1/sync/mark-failed/sync-fail", json={"error": "timeout"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_retry_failed(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [
            _make_sync_queue(id="sync-fail", status="failed", retry_count=1, error="timeout"),
        ]
        mock_session.execute.return_value = mr
        mock_session.commit = AsyncMock()

        resp = await client.post("/api/v1/sync/retry-failed", json={"max_retries": 3})
        assert resp.status_code == 200
        assert "retried" in resp.json()

    @pytest.mark.asyncio
    async def test_sync_status(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = _make_sync_queue(idempotency_key="idem-lookup")
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/sync/status/idem-lookup")
        assert resp.status_code == 200
        assert resp.json()["idempotency_key"] == "idem-lookup"


class TestSyncStaffAccess:
    """Field staff (vet/surgeon) must be able to drive their own sync queue;
    the offline-first flow cannot require an admin on every device."""

    @pytest.fixture
    def auth_override(self):
        def _override():
            return TokenPayload(user_id="vet-1", role="vet")
        return _override

    @pytest.mark.asyncio
    async def test_enqueue_allowed_for_staff(self, client: AsyncClient, mock_session: AsyncMock):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = None  # no idempotency conflict
        mock_session.execute.return_value = mr
        mock_session.commit = AsyncMock()
        async def mock_refresh(obj):
            if hasattr(obj, "id") and obj.id is None:
                obj.id = "sync-new"
        mock_session.refresh = AsyncMock(side_effect=mock_refresh)

        resp = await client.post("/api/v1/sync/enqueue", json={
            "entity_type": "surgery",
            "entity_id": "surg-1",
            "operation": "create",
            "payload": {"surgery_type": "spay"},
            "idempotency_key": "idem-vet",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_mark_synced_sets_timestamp(self, client: AsyncClient, mock_session: AsyncMock):
        """Regression: synced_at must reflect the actual sync moment."""
        item = _make_sync_queue()
        _setup_sync_lookup(mock_session, item)
        mock_session.commit = AsyncMock()

        resp = await client.post("/api/v1/sync/mark-synced/sync-1")
        assert resp.status_code == 200
        assert item.synced_at is not None

    @pytest.mark.asyncio
    async def test_mark_failed_records_error(self, client: AsyncClient, mock_session: AsyncMock):
        item = _make_sync_queue()
        _setup_sync_lookup(mock_session, item)
        mock_session.commit = AsyncMock()

        resp = await client.post(
            "/api/v1/sync/mark-failed/sync-fail", json={"error": "timeout"}
        )
        assert resp.status_code == 200
        assert item.error == "timeout"

    @pytest.mark.asyncio
    async def test_reads_allowed_for_staff(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [_make_sync_queue()]
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/sync/pending")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_retry_failed_allowed_for_staff(self, client: AsyncClient, mock_session: AsyncMock):
        """Retry is a field-device operation; staff may trigger it."""
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr
        mock_session.commit = AsyncMock()

        resp = await client.post(
            "/api/v1/sync/retry-failed", json={"max_retries": 3}
        )
        assert resp.status_code == 200
        assert resp.json() == {"retried": 0}
