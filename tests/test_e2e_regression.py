"""End-to-end regression tests against a real PostgreSQL database.

These tests exercise true HTTP flows — cookies, FK constraints, cross-centre
authorization, real file bytes — that mocked-session tests cannot catch.

Requires: Docker Postgres (abc/abc) with an `abc_test` database.
    docker exec <db-container> psql -U abc -d postgres \\
        -c "CREATE DATABASE abc_test OWNER abc;"

Run:
    DATABASE_URL=postgresql+asyncpg://abc:abc@localhost:5433/abc_test \\
        pytest tests/test_e2e_regression.py -v

Skipped automatically (not failed) when the database is unreachable, so the
mocked suite keeps passing on machines without Docker.
"""
from __future__ import annotations

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.auth.deps import hash_password
from src.auth.routes import limiter as auth_limiter
from src.database import get_db
from src.main import app as _app
from src.main import limiter, public_limiter
from src.models.base import Allocation, Centre, Grant, Staff

TEST_DATABASE_URL = os.environ.get(
    "E2E_DATABASE_URL",
    "postgresql+asyncpg://abc:abc@localhost:5433/abc_test",
)

pytestmark = pytest.mark.e2e


def _phone() -> str:
    """Unique 10-digit phone per call (unique constraint safety)."""
    return f"9{uuid4().hex[:9]}"


@pytest.fixture
async def session_maker():
    engine = create_async_engine(TEST_DATABASE_URL)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        await engine.dispose()
        pytest.skip(f"test database unreachable at {TEST_DATABASE_URL}")

    from src.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    yield maker
    await engine.dispose()


@pytest.fixture
async def client(session_maker):
    async def _override():
        async with session_maker() as session:
            yield session

    _app.dependency_overrides.clear()
    _app.dependency_overrides[get_db] = _override
    limiter.reset()
    auth_limiter.reset()
    public_limiter.reset()
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="https://test") as c:
        yield c
    _app.dependency_overrides.clear()


async def _seed_staff(maker, *, phone: str, role: str = "vet", centre_id=None,
                      active: bool = True, name: str = "Dr Seed") -> str:
    async with maker() as s:
        staff = Staff(
            name=name, phone=phone, role=role, centre_id=centre_id,
            password_hash=hash_password("secret123"), active=active,
        )
        s.add(staff)
        await s.commit()
        await s.refresh(staff)
        return staff.id


async def _seed_centre(maker, *, code: str, state: str = "Rajasthan") -> str:
    async with maker() as s:
        centre = Centre(name=f"Centre {code}", code=code, district="Jaipur",
                        state=state, capacity=50)
        s.add(centre)
        await s.commit()
        await s.refresh(centre)
        return centre.id


async def _seed_allocation(maker, *, centre_id: str, amount: str = "100000") -> str:
    async with maker() as s:
        grant = Grant(awbi_ref=f"AWBI-{uuid4().hex[:8].upper()}", amount="500000",
                      purpose="ABC program", financial_year="2026-27")
        s.add(grant)
        await s.commit()
        await s.refresh(grant)
        alloc = Allocation(grant_id=grant.id, centre_id=centre_id, amount=amount)
        s.add(alloc)
        await s.commit()
        await s.refresh(alloc)
        return alloc.id


async def _login(client: AsyncClient, phone: str) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": "secret123"},
    )
    assert resp.status_code == 200, f"login failed: {resp.status_code} {resp.text}"


class TestCookieAuth:
    async def test_cookie_only_request_is_authenticated(self, client, session_maker):
        """Regression: cookie-based auth must work without a Bearer header."""
        phone = _phone()
        await _seed_staff(session_maker, phone=phone)
        await _login(client, phone)

        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["phone"] == phone
        assert body["role"] == "vet"

    async def test_no_credentials_rejected(self, client):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_export_endpoints_accept_cookie_auth(self, client, session_maker):
        """Regression: PDF/Excel export must work with cookie auth only.

        The frontend sends no Authorization header on export; before the
        cookie fallback these routes 401'd in every cookie-authenticated
        session (i.e. all of production).
        """
        phone = _phone()
        await _seed_staff(session_maker, phone=phone, role="admin")
        await _login(client, phone)

        payload = {
            "template_id": "TMPL-001",
            "date_range": "Last 30 Days",
            "region": "All India",
            "metric": "Overall Compliance %",
        }
        pdf = await client.post("/api/v1/reports/export/pdf", json=payload)
        assert pdf.status_code == 200
        assert pdf.content[:4] == b"%PDF"

        xls = await client.post("/api/v1/reports/export/excel", json=payload)
        assert xls.status_code == 200
        # xlsx is a ZIP container
        assert xls.content[:2] == b"PK"


class TestComplaintValidation:
    async def test_invalid_centre_returns_400_not_500(self, client):
        """Regression: public endpoint must not leak 500s on bad input."""
        resp = await client.post(
            "/api/v1/public/complaints",
            json={"centre_id": "no-such-centre", "citizen_phone": "9876500000",
                  "description": "Stray dog injured near market"},
        )
        assert resp.status_code == 400
        assert "centre" in resp.json()["detail"].lower()

    async def test_valid_complaint_is_201(self, client, session_maker):
        centre_id = await _seed_centre(session_maker, code=f"C{uuid4().hex[:6].upper()}")
        resp = await client.post(
            "/api/v1/public/complaints",
            json={"centre_id": centre_id, "citizen_phone": "9876500001",
                  "description": "Stray dog injured near market"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "open"


class TestExpenseScoping:
    async def _centres_and_alloc(self, session_maker):
        centre_a = await _seed_centre(session_maker, code=f"A{uuid4().hex[:6].upper()}")
        centre_b = await _seed_centre(session_maker, code=f"B{uuid4().hex[:6].upper()}")
        alloc_b = await _seed_allocation(session_maker, centre_id=centre_b)
        return centre_a, centre_b, alloc_b

    async def test_vet_cannot_bill_other_centres_allocation(self, client, session_maker):
        """Regression (IDOR): vets may only bill against their own centre."""
        centre_a, _centre_b, alloc_b = await self._centres_and_alloc(session_maker)
        phone = _phone()
        await _seed_staff(session_maker, phone=phone, centre_id=centre_a)
        await _login(client, phone)

        resp = await client.post(
            "/api/v1/expenses",
            json={"allocation_id": alloc_b, "category": "medicines", "amount": "500"},
        )
        assert resp.status_code == 403

    async def test_vet_can_bill_own_centres_allocation(self, client, session_maker):
        centre_a = await _seed_centre(session_maker, code=f"A{uuid4().hex[:6].upper()}")
        alloc_a = await _seed_allocation(session_maker, centre_id=centre_a)
        phone = _phone()
        await _seed_staff(session_maker, phone=phone, centre_id=centre_a)
        await _login(client, phone)

        resp = await client.post(
            "/api/v1/expenses",
            json={"allocation_id": alloc_a, "category": "medicines", "amount": "500"},
        )
        assert resp.status_code == 201
        assert float(resp.json()["amount"]) == 500.0

    async def test_admin_can_bill_any_centre(self, client, session_maker):
        _centre_a, _centre_b, alloc_b = await self._centres_and_alloc(session_maker)
        phone = _phone()
        await _seed_staff(session_maker, phone=phone, role="admin")
        await _login(client, phone)

        resp = await client.post(
            "/api/v1/expenses",
            json={"allocation_id": alloc_b, "category": "medicines", "amount": "500"},
        )
        assert resp.status_code == 201


class TestCrossCentreIsolation:
    async def test_vet_cannot_create_dog_in_other_centre(self, client, session_maker):
        """Pin existing centre-scoping on a real database."""
        centre_a = await _seed_centre(session_maker, code=f"A{uuid4().hex[:6].upper()}")
        centre_b = await _seed_centre(session_maker, code=f"B{uuid4().hex[:6].upper()}")
        phone = _phone()
        await _seed_staff(session_maker, phone=phone, centre_id=centre_a)
        await _login(client, phone)

        resp = await client.post(
            "/api/v1/dogs",
            json={"centre_id": centre_b, "tag_id": f"TAG-{uuid4().hex[:6]}",
                  "sex": "female"},
        )
        assert resp.status_code == 403


class TestAuthLifecycle:
    """Full lifecycle: register → pending → admin approves → login works."""

    async def test_register_login_pending_approval_flow(self, client, session_maker):
        phone = _phone()
        # 1. Register — must NOT yield a session
        reg = await client.post("/api/v1/auth/register", json={
            "name": "Dr Pending", "phone": phone, "password": "secret123",
        })
        assert reg.status_code == 202
        assert reg.json()["status"] == "pending_approval"
        staff_id = reg.json()["id"]

        # 2. Login before approval must be blocked
        early = await client.post(
            "/api/v1/auth/login", json={"phone": phone, "password": "secret123"},
        )
        assert early.status_code == 403

        # 3. Admin activates
        await _seed_staff(session_maker, phone=_phone(), role="admin")
        admin_phone_holder = None
        maker_session = session_maker()
        async with maker_session as s:
            result = await s.execute(text("SELECT phone FROM staff WHERE role='admin'"))
            admin_phone_holder = result.scalar_one()

        await client.post(
            "/api/v1/auth/login",
            json={"phone": admin_phone_holder, "password": "secret123"},
        )
        approve = await client.patch(
            f"/api/v1/auth/staff/{staff_id}", json={"active": True},
        )
        assert approve.status_code == 200

        # 4. Login now succeeds; /me reflects the session
        final = await client.post(
            "/api/v1/auth/login", json={"phone": phone, "password": "secret123"},
        )
        assert final.status_code == 200

        me = await client.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["phone"] == phone

    async def test_admin_cannot_deactivate_last_admin(self, client, session_maker):
        admin_phone = _phone()
        await _seed_staff(session_maker, phone=admin_phone, role="admin", name="Solo Admin")

        await _login(client, admin_phone)
        me_resp = await client.get("/api/v1/auth/me")
        my_id = me_resp.json()["user_id"]

        resp = await client.patch(f"/api/v1/auth/staff/{my_id}", json={"active": False})
        assert resp.status_code == 409
        assert "last active admin" in resp.json()["detail"]

    async def test_nonadmin_cannot_access_staff_management(self, client, session_maker):
        phone = _phone()
        centre_id = await _seed_centre(session_maker, code=f"C{uuid4().hex[:6].upper()}")
        await _seed_staff(session_maker, phone=phone, centre_id=centre_id)
        await _login(client, phone)

        resp = await client.get("/api/v1/auth/staff")
        assert resp.status_code == 403

    async def test_deactivate_revokes_refresh(self, client, session_maker):
        """Deactivated user's existing refresh token must stop working."""
        from httpx import ASGITransport, AsyncClient as AC

        phone = _phone()
        staff_id = await _seed_staff(session_maker, phone=phone)
        # Vet logs in on their own client so their cookie jar is independent
        vet_transport = ASGITransport(app=_app)
        async with AC(transport=vet_transport, base_url="https://test") as vet_client:
            await _login(vet_client, phone)

            # Admin (on the shared client) deactivates the vet
            admin_phone = _phone()
            await _seed_staff(session_maker, phone=admin_phone, role="admin")
            await _login(client, admin_phone)
            deact = await client.patch(f"/api/v1/auth/staff/{staff_id}", json={"active": False})
            assert deact.status_code == 200

            # The vet's refresh cookie is now worthless (token_version bumped)
            refresh = await vet_client.post("/api/v1/auth/refresh")
            assert refresh.status_code == 401


class TestHealthRealDB:
    async def test_health_with_real_database(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
        assert resp.json()["checks"]["database"] is True
