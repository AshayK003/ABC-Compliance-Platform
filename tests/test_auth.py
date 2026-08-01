from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import (
    TokenPayload,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
)
from src.config import settings
from src.database import get_db
from src.main import app as _app
from src.models.base import Staff


@pytest.fixture
def app() -> FastAPI:
    _app.dependency_overrides.clear()
    return _app


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
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


def _make_staff(**kwargs) -> Staff:
    data = {
        "id": "staff-1",
        "centre_id": None,
        "name": "Dr. Test",
        "role": "vet",
        "phone": "9876543210",
        "password_hash": hash_password("secret123"),
        "active": True,
    }
    data.update(kwargs)
    return Staff(**data)


def _setup_mock_execute(mock_session: AsyncMock, return_value):
    """Helper to properly setup mock execute with scalar_one_or_none"""
    mr = MagicMock()
    mr.scalar_one_or_none.return_value = return_value
    mock_session.execute.return_value = mr
    return mr


class TestRegister:
    @pytest.mark.asyncio
    async def test_registers_new_staff(self, client: AsyncClient, mock_session: AsyncMock):
        _setup_mock_execute(mock_session, None)
        mock_session.commit = AsyncMock()
        # Mock refresh to set ID on the staff object - but we can't easily test the response body
        # since the staff object is created inside the route handler. Just verify status and cookies.
        async def mock_refresh(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = "staff-new-id"
        mock_session.refresh = AsyncMock(side_effect=mock_refresh)

        resp = await client.post("/auth/register", json={
            "name": "Dr. Test",
            "phone": "9876543210",
            "password": "secret123",
            "role": "vet",
        })
        assert resp.status_code == 201
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_duplicate_phone(self, client: AsyncClient, mock_session: AsyncMock):
        _setup_mock_execute(mock_session, _make_staff())

        resp = await client.post("/auth/register", json={
            "name": "Dr. Test",
            "phone": "9876543210",
            "password": "secret123",
        })
        assert resp.status_code == 409
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_validates_payload(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={"phone": "123"})
        assert resp.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_returns_token(self, client: AsyncClient, mock_session: AsyncMock):
        _setup_mock_execute(mock_session, _make_staff())

        resp = await client.post("/auth/login", json={
            "phone": "9876543210",
            "password": "secret123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["role"] == "vet"
        assert body["access_token"]
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, mock_session: AsyncMock):
        _setup_mock_execute(mock_session, _make_staff(password_hash=hash_password("other")))

        resp = await client.post("/auth/login", json={
            "phone": "9876543210",
            "password": "secret123",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_phone(self, client: AsyncClient, mock_session: AsyncMock):
        _setup_mock_execute(mock_session, None)

        resp = await client.post("/auth/login", json={
            "phone": "0000000000",
            "password": "whatever",
        })
        assert resp.status_code == 401


class TestMe:
    @pytest.mark.asyncio
    async def test_returns_current_user(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 200
        assert resp.json() == {"user_id": "test-user-id", "role": "admin"}


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, mock_session: AsyncMock, app: FastAPI):
        def vet_override():
            return TokenPayload(user_id="staff-1", role="vet")
        app.dependency_overrides[get_current_user] = vet_override

        _setup_mock_execute(mock_session, _make_staff())

        client.cookies.set("refresh_token", create_refresh_token("staff-1"))

        resp = await client.post("/auth/refresh")
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["role"] == "vet"
        assert body["access_token"]
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_clears_cookies(self, client: AsyncClient):
        resp = await client.post("/auth/logout")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Logged out"}
        # Cookies should be cleared (deleted) via Set-Cookie headers
        set_cookie = resp.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "refresh_token=" in set_cookie
        assert "Max-Age=0" in set_cookie


class TestDeleteAccount:
    @pytest.mark.asyncio
    async def test_delete_account(self, client: AsyncClient, mock_session: AsyncMock, app: FastAPI):
        def vet_override():
            return TokenPayload(user_id="staff-1", role="vet")
        app.dependency_overrides[get_current_user] = vet_override
        
        _setup_mock_execute(mock_session, _make_staff())
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()

        resp = await client.delete("/auth/me")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Account deleted"}
        # Cookies should be cleared (deleted) via Set-Cookie headers
        set_cookie = resp.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "refresh_token=" in set_cookie
        assert "Max-Age=0" in set_cookie
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_awaited_once()


class TestTokenDecode:
    def test_expired_token_rejected(self):
        now = datetime.now(UTC)
        payload = {
            "sub": "user-1",
            "role": "admin",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            decode_token(token)
        assert exc.value.status_code == 401

    def test_invalid_signature_rejected(self):
        payload = {"sub": "user-1", "role": "admin"}
        token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            decode_token(token)
        assert exc.value.status_code == 401