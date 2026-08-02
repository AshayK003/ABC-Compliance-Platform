from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user
from src.database import get_db
from src.main import app as _app
from src.models.base import Dog


@pytest.fixture
def app() -> FastAPI:
    """Return the app with overridden dependencies for testing."""
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


def _make_dog(**kwargs) -> Dog:
    """Build a real Dog model instance for test assertions."""
    data = {
        "id": "dog-1",
        "centre_id": "centre-1",
        "tag_id": "ABC-001",
        "sex": "male",
        "age_estimate": 3,
        "weight": 15.5,
        "status": "registered",
    }
    data.update(kwargs)
    return Dog(**data)


class TestCreateDog:
    @pytest.mark.asyncio
    async def test_creates_and_returns_dog(self, client: AsyncClient, mock_session: AsyncMock):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        payload = {
            "centre_id": "centre-1",
            "tag_id": "ABC-001",
            "sex": "male",
            "age_estimate": 3,
            "weight": 15.5,
        }

        resp = await client.post("/api/v1/dogs", json=payload)

        assert resp.status_code == 201
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_requires_tag_id_and_sex(self, client: AsyncClient):
        resp = await client.post("/api/v1/dogs", json={"centre_id": "centre-1"})
        assert resp.status_code == 422


class TestListDogs:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, client: AsyncClient, mock_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/dogs")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_dogs(self, client: AsyncClient, mock_session: AsyncMock):
        d1 = _make_dog(id="d1", tag_id="ABC-001", sex="male")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [d1]
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/dogs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tag_id"] == "ABC-001"

    @pytest.mark.asyncio
    async def test_filters_by_centre_id(self, client: AsyncClient, mock_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/dogs?centre_id=centre-1")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_filters_by_status(self, client: AsyncClient, mock_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/dogs?status=registered")
        assert resp.status_code == 200


class TestGetDog:
    @pytest.mark.asyncio
    async def test_returns_dog_by_id(self, client: AsyncClient, mock_session: AsyncMock):
        d1 = _make_dog(id="dog-1", tag_id="ABC-001", sex="male")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = d1
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/dogs/dog-1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "dog-1"

    @pytest.mark.asyncio
    async def test_404_for_missing(self, client: AsyncClient, mock_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        resp = await client.get("/api/v1/dogs/nonexistent")
        assert resp.status_code == 404
