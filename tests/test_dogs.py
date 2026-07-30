from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.database import get_db
from src.main import app as _app
from src.models.base import Dog


@pytest.fixture
def app():
    _app.dependency_overrides.clear()
    return _app


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def auth_override():
    def _override():
        from src.auth.deps import TokenPayload
        return TokenPayload(user_id="test-user-id", role="admin")
    return _override


@pytest.fixture
async def client(app, mock_session, auth_override):
    from src.auth.deps import get_current_user
    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_current_user] = auth_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_dog(**kwargs) -> Dog:
    data = {
        "centre_id": "centre-1",
        "tag_id": "TAG-001",
        "sex": "female",
        "age_estimate": 3,
        "weight": 18.0,
        "status": "registered",
    }
    data.update(kwargs)
    return Dog(**data)


class TestCreateDog:
    @pytest.mark.asyncio
    async def test_creates_and_returns_dog(self, client, mock_session):
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        resp = await client.post("/dogs", json={
            "centre_id": "centre-1",
            "tag_id": "TAG-001",
            "sex": "female",
        })
        assert resp.status_code == 201
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_requires_tag_id(self, client):
        resp = await client.post("/dogs", json={"centre_id": "centre-1", "sex": "female"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_requires_sex(self, client):
        resp = await client.post("/dogs", json={"centre_id": "centre-1", "tag_id": "TAG-001"})
        assert resp.status_code == 422


class TestListDogs:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, client, mock_session):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/dogs")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_dogs(self, client, mock_session):
        d1 = _make_dog(id="dog-1", tag_id="TAG-001")
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = [d1]
        mock_session.execute.return_value = mr

        resp = await client.get("/dogs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tag_id"] == "TAG-001"

    @pytest.mark.asyncio
    async def test_filters_by_centre_id(self, client, mock_session):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/dogs?centre_id=centre-1")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_filters_by_status(self, client, mock_session):
        mr = MagicMock()
        mr.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mr

        resp = await client.get("/dogs?status=registered")
        assert resp.status_code == 200


class TestGetDog:
    @pytest.mark.asyncio
    async def test_returns_dog_by_id(self, client, mock_session):
        d1 = _make_dog(id="dog-1", tag_id="TAG-001")
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = d1
        mock_session.execute.return_value = mr

        resp = await client.get("/dogs/dog-1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "dog-1"

    @pytest.mark.asyncio
    async def test_404_for_missing(self, client, mock_session):
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mr

        resp = await client.get("/dogs/nonexistent")
        assert resp.status_code == 404
