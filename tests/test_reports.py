from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user
from src.database import get_db
from src.main import app as _app


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
        return TokenPayload(user_id="test-user-id", role="admin")
    return _override


@pytest.fixture
async def client(app: FastAPI, mock_session: AsyncMock, auth_override) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_user] = auth_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestGenerateReport:
    @pytest.mark.asyncio
    async def test_generate_monthly_compliance_succeeds(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        # All three TMPL-001 queries return empty results.
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mr.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.post(
            "/api/v1/reports/generate",
            json={"template_id": "TMPL-001", "format": "json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["template_id"] == "TMPL-001"
        assert data["generated_at"]  # datetime.now(UTC) must not raise NameError
        assert data["preview_data"] == []

    @pytest.mark.asyncio
    async def test_unknown_template_returns_404(
        self, client: AsyncClient, mock_session: AsyncMock
    ):
        resp = await client.post(
            "/api/v1/reports/generate",
            json={"template_id": "TMPL-999", "format": "json"},
        )
        assert resp.status_code == 404
