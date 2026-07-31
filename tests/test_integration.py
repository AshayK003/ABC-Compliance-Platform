from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.auth.deps import TokenPayload, get_current_user
from src.database import get_db
from src.main import app as _app
from src.models.base import Base

# This test requires a real DATABASE_URL env var pointing to a Postgres instance
# It's skipped by default unless RUN_INTEGRATION=1 is set
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION"),
    reason="Set RUN_INTEGRATION=1 to run integration tests against real DB",
)


@pytest.fixture
def engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return create_async_engine(url)


@pytest.fixture
async def setup_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(engine, setup_db):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def app(db_session):
    _app.dependency_overrides.clear()
    _app.dependency_overrides[get_db] = lambda: db_session

    def auth_override():
        return TokenPayload(user_id="test-user", role="admin")

    _app.dependency_overrides[get_current_user] = auth_override
    return _app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAuthIntegration:
    @pytest.mark.asyncio
    async def test_register_and_login(self, client: AsyncClient):
        # Register
        resp = await client.post("/auth/register", json={
            "name": "Test Vet",
            "phone": "9999999999",
            "password": "testpass123",
            "role": "vet",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["role"] == "vet"
        assert "id" in data

        # Login
        resp = await client.post("/auth/login", json={
            "phone": "9999999999",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "vet"


class TestCentresIntegration:
    @pytest.mark.asyncio
    async def test_create_and_list_centres(self, client: AsyncClient):
        # Create centre
        resp = await client.post("/centres", json={
            "name": "BBMP Centre 1",
            "code": "BBMP001",
            "district": "Bangalore Urban",
            "state": "Karnataka",
            "capacity": 50,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "BBMP001"
        centre_id = data["id"]

        # List centres
        resp = await client.get("/centres")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == centre_id


class TestSyncQueueIntegration:
    @pytest.mark.asyncio
    async def test_enqueue_and_list(self, client: AsyncClient):
        # Enqueue
        resp = await client.post("/sync/enqueue", json={
            "entity_type": "surgery",
            "entity_id": "surgery-123",
            "operation": "create",
            "payload": {"dog_id": "dog-1"},
            "idempotency_key": "test-key-1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["idempotency_key"] == "test-key-1"
        sync_id = data["id"]

        # List pending
        resp = await client.get("/sync/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == sync_id


class TestComplaintsIntegration:
    @pytest.mark.asyncio
    async def test_create_and_update_complaint(self, client: AsyncClient):
        # Create a real centre first (FK constraint on complaints.centre_id)
        resp = await client.post("/centres", json={
            "name": "BBMP Centre 2",
            "code": "BBMP002",
            "district": "Bangalore Urban",
            "state": "Karnataka",
            "capacity": 40,
        })
        assert resp.status_code == 201
        centre_id = resp.json()["id"]

        # Create complaint (public endpoint - no auth needed, but works through same client)
        resp = await client.post("/public/complaints", json={
            "centre_id": centre_id,
            "citizen_phone": "9876543210",
            "description": "Test complaint",
        })
        assert resp.status_code == 201
        complaint_id = resp.json()["id"]

        # Update complaint (requires auth)
        resp = await client.patch(f"/public/complaints/{complaint_id}", json={
            "status": "resolved",
            "resolution": "Fixed",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"
