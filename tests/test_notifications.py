from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user
from src.database import get_db
from src.main import app as _app
from src.models.base import Notification


@pytest.fixture
def app() -> FastAPI:
    _app.dependency_overrides.clear()
    return _app


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def auth_override():
    def _override():
        return TokenPayload(user_id="user-a", role="vet")
    return _override


@pytest.fixture
async def client(app: FastAPI, mock_session: AsyncMock, auth_override) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_user] = auth_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_notification(**kwargs) -> Notification:
    data = {
        "id": "notif-1",
        "user_id": "user-a",
        "title": "Test",
        "message": "Hello",
        "type": "info",
        "read": False,
    }
    data.update(kwargs)
    return Notification(**data)


class TestListNotificationsScoping:
    @pytest.mark.asyncio
    async def test_lists_own_notifications(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [_make_notification()]
        mock_session.execute.return_value = mr

        # Passing another user's id must be ignored for non-admin callers.
        resp = await client.get("/api/v1/notifications?user_id=user-b")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["user_id"] == "user-a"

    @pytest.mark.asyncio
    async def test_unread_count_scoped_to_caller(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        mr = MagicMock()
        mr.scalar.return_value = 3
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/notifications/unread-count?user_id=user-b")
        assert resp.status_code == 200
        assert resp.json() == {"count": 3}


class TestNotificationOwnership:
    @pytest.mark.asyncio
    async def test_get_foreign_notification_returns_404(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = _make_notification(user_id="user-b")
        mock_session.execute.return_value = mr

        resp = await client.get("/api/v1/notifications/notif-1")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_foreign_notification_returns_404(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = _make_notification(user_id="user-b")
        mock_session.execute.return_value = mr

        resp = await client.patch(
            "/api/v1/notifications/notif-1", json={"read": True}
        )
        assert resp.status_code == 404
