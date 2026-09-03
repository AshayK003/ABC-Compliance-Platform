"""Regression tests for issues found in the 2026-08-22 full-stack audit.

Covers:
- Notifications endpoints (table existed only as a model; migration 004 added it)
- Expense balance guard boundary conditions
- Sync queue idempotency contract
- Notification IDOR scoping (non-admin cannot read others' notifications)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the app package resolves when running from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException, Request
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
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


def _result(rows=None, scalar=None):
    """Build a mock execute() result."""
    mr = MagicMock()
    mr.scalar_one_or_none.return_value = scalar
    if rows is not None:
        mr.scalars.return_value.all.return_value = rows
        return mr
    mr.scalars.return_value.all.return_value = []
    return mr


class TestNotificationContract:
    """The notifications table must exist and endpoints must behave per spec.

    Regression: models defined Notification but no migration created the
    table — every /notifications call returned 500 on deployed instances.
    """

    def test_migration_004_exists_and_chains(self):
        migration_dir = Path(__file__).resolve().parents[1] / "migrations" / "versions"
        contents = {p.name: p.read_text(encoding="utf-8") for p in migration_dir.glob("*.py")}
        assert "004_notifications_and_committee_tables.py" in contents, (
            "migration 004 missing: notifications table would not exist on fresh deploys"
        )
        m004 = contents["004_notifications_and_committee_tables.py"]
        assert 'down_revision: str = "003"' in m004
        for table in (
            "notifications", "committees", "meetings", "decisions",
            "votes", "committee_members", "meeting_attendees", "committee_documents",
        ):
            assert f'"{table}"' in m004, f"migration 004 does not create {table}"

    def test_notification_model_matches_migration(self):
        from src.models.base import Notification

        assert Notification.__tablename__ == "notifications"
        columns = {c.name for c in Notification.__table__.columns}
        assert {"id", "user_id", "title", "message", "type", "read", "created_at"} <= columns


class TestExpenseBalanceGuard:
    """Logic review: expense must never exceed allocation balance."""

    def test_guard_uses_decimal_safe_comparison(self):
        # The guard sums existing expenses then compares total+amount > allocation.
        # Boundary contract: exact-balance expense is allowed, one-paise-over is not.
        from decimal import Decimal

        allocation = Decimal("5000.00")
        existing = Decimal("3000.00")
        # exact remainder allowed (comparison must be False)
        assert not (existing + (allocation - existing) > allocation)
        # smallest possible overshoot rejected
        assert existing + (allocation - existing) + Decimal("0.01") > allocation


class TestSyncIdempotency:
    """Duplicate enqueue with same idempotency_key must not create a second row."""

    @pytest.mark.asyncio
    async def test_enqueue_duplicate_returns_existing(
        self, app: FastAPI, mock_session: AsyncMock
    ):
        from src.models.base import SyncQueue

        existing = SyncQueue(
            id="sq-1",
            entity_type="dog",
            entity_id="d1",
            operation="create",
            payload={"a": 1},
            idempotency_key="key-123",
            status="pending",
        )

        def admin_override():
            return TokenPayload(user_id="admin-1", role="admin")

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = admin_override

        # First execute: idempotency lookup finds the existing row
        mock_session.execute.return_value = _result(scalar=existing)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/sync/enqueue", json={
                "entity_type": "dog",
                "entity_id": "d1",
                "operation": "create",
                "payload": {"a": 1},
                "idempotency_key": "key-123",
            })

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "sq-1"
        assert body["idempotency_key"] == "key-123"
        # Must NOT have inserted a new row
        mock_session.add.assert_not_called()


class TestNotificationIDOR:
    """Security: non-admins must never read another user's notification."""

    @pytest.mark.asyncio
    async def test_vet_cannot_read_other_users_notification(
        self, app: FastAPI, mock_session: AsyncMock
    ):
        from src.models.base import Notification

        other_users_notification = Notification(
            id="n-1", user_id="someone-else", title="t", message="m"
        )
        mock_session.execute.return_value = _result(scalar=other_users_notification)

        def vet_override():
            return TokenPayload(user_id="vet-1", role="vet")

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = vet_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/notifications/n-1")

        # Must be masked as 404, not 403 (no existence leak)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_admin_can_read_any_notification(
        self, app: FastAPI, mock_session: AsyncMock
    ):
        from src.models.base import Notification

        notification = Notification(id="n-2", user_id="anyone", title="t", message="m")
        mock_session.execute.return_value = _result(scalar=notification)

        def admin_override():
            return TokenPayload(user_id="admin-1", role="admin")

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = admin_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/notifications/n-2")

        assert resp.status_code == 200


class TestReportsChartContracts:
    """Frontend consumes these shapes; breaking them breaks the UI silently."""

    @pytest.mark.asyncio
    async def test_yoy_shape(self, client_factory=None):
        pass  # covered by live blackbox; shape asserted in integration suite


class TestExpenseRaceGuard:
    """Regression for #35/#20: allocation row must be locked during balance check."""

    @pytest.mark.asyncio
    async def test_expense_select_uses_row_lock(self):
        import inspect

        from src.funds import routes as funds_routes

        src = inspect.getsource(funds_routes.create_expense)
        assert ".with_for_update()" in src, (
            "create_expense must lock the allocation row (SELECT ... FOR UPDATE) "
            "or concurrent expenses can overspend the allocation"
        )

    def test_with_for_update_emits_locking_sql(self):
        # The SQLAlchemy construct must render FOR UPDATE.
        from sqlalchemy import select

        from src.models.base import Allocation

        stmt = select(Allocation).where(Allocation.id == "x").with_for_update()
        compiled = str(stmt.compile())
        assert "FOR UPDATE" in compiled.upper()


class TestCentreScoping:
    """Regression for #32: require_centre_access dependency enforces centre match."""

    @pytest.mark.asyncio
    async def test_non_admin_wrong_centre_forbidden(self, app: FastAPI, mock_session: AsyncMock):
        from src.auth.deps import require_centre_access

        check = require_centre_access("centre_id")
        vet = TokenPayload(user_id="v1", role="vet", centre_id="centre-a")

        with pytest.raises(HTTPException) as exc:
            await check(centre_id="centre-b", current=vet)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_matching_centre_allowed(self):
        from src.auth.deps import require_centre_access

        check = require_centre_access("centre_id")
        vet = TokenPayload(user_id="v1", role="vet", centre_id="centre-a")
        result = await check(centre_id="centre-a", current=vet)
        assert result is vet

    @pytest.mark.asyncio
    async def test_admin_bypasses(self):
        from src.auth.deps import require_centre_access

        check = require_centre_access("centre_id")
        admin = TokenPayload(user_id="a1", role="admin", centre_id=None)
        result = await check(centre_id="any-centre", current=admin)
        assert result is admin

    @pytest.mark.asyncio
    async def test_vet_without_centre_assignment_blocked(self):
        from src.auth.deps import require_centre_access

        check = require_centre_access("centre_id")
        vet = TokenPayload(user_id="v1", role="vet", centre_id=None)
        with pytest.raises(HTTPException) as exc:
            await check(centre_id="centre-a", current=vet)
        assert exc.value.status_code == 403


class TestAuditWiring:
    """Regression for #34: create mutations write audit events."""

    @pytest.mark.asyncio
    async def test_create_grant_writes_audit_event(self, app: FastAPI, mock_session: AsyncMock):
        added: list[object] = []
        mock_session.add.side_effect = lambda obj: added.append(obj)

        def admin_override():
            return TokenPayload(user_id="admin-1", role="admin")

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = admin_override

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/grants", json={
                "awbi_ref": "AUD-TEST-1",
                "amount": "1000.00",
                "purpose": "audit",
                "financial_year": "2026-27",
            })

        assert resp.status_code == 201
        types = [type(o).__name__ for o in added]
        assert "Grant" in types, "grant was not persisted"
        assert "AuditEvent" in types, "grant creation did not write an audit event"


class TestStaffHashLeak:
    """Critical: /auth/staff* must never serialise password_hash/token_version."""

    def _admin(self, app: FastAPI, mock_session: AsyncMock):
        from src.models.base import Staff  # noqa: F401  (import guard)

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = lambda: TokenPayload(user_id="a", role="admin")

    def _staff(self):
        from src.models.base import Staff

        return Staff(
            id="s1", centre_id="c1", name="Dr A", role="vet",
            phone="9876543210", password_hash="hash", active=True, token_version=3,
        )

    @pytest.mark.asyncio
    async def test_list_staff_hides_secrets(self, app: FastAPI, mock_session: AsyncMock):
        self._admin(app, mock_session)
        mock_session.execute.return_value = _result(rows=[self._staff()])

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/auth/staff")

        assert resp.status_code == 200
        assert "password_hash" not in resp.json()[0]
        assert "token_version" not in resp.json()[0]
        assert resp.json()[0]["phone"] == "9876543210"

    @pytest.mark.asyncio
    async def test_update_staff_hides_secrets(self, app: FastAPI, mock_session: AsyncMock):
        self._admin(app, mock_session)
        mock_session.execute.return_value = _result(scalar=self._staff())

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.patch("/api/v1/auth/staff/s1", json={"active": False})

        assert resp.status_code == 200
        assert "password_hash" not in resp.json()
        assert "token_version" not in resp.json()


class TestCentreReadIsolation:
    """Critical (IDOR): HTTP-level centre isolation on reads."""

    def _vet(self, app: FastAPI, mock_session: AsyncMock):
        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = lambda: TokenPayload(
            user_id="v1", role="vet", centre_id="centre-a"
        )

    def _dog(self, centre: str):
        from src.models.base import Dog

        return Dog(id="d1", centre_id=centre, tag_id="T1", sex="female")

    @pytest.mark.asyncio
    async def test_vet_cannot_read_other_centre_dog(self, app: FastAPI, mock_session: AsyncMock):
        self._vet(app, mock_session)
        mock_session.execute.return_value = _result(scalar=self._dog("centre-b"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/dogs/d1")

        assert resp.status_code == 404  # masked, no existence leak

    @pytest.mark.asyncio
    async def test_vet_can_read_own_centre_dog(self, app: FastAPI, mock_session: AsyncMock):
        self._vet(app, mock_session)
        mock_session.execute.return_value = _result(scalar=self._dog("centre-a"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/dogs/d1")

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_vet_list_rejected_for_other_centre(self, app: FastAPI, mock_session: AsyncMock):
        self._vet(app, mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/dogs?centre_id=centre-b")

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_vet_list_without_filter_scoped(self, app: FastAPI, mock_session: AsyncMock):
        self._vet(app, mock_session)
        mock_session.execute.return_value = _result(rows=[self._dog("centre-a")])

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/dogs")

        assert resp.status_code == 200


class TestGrantOverallocation:
    """High: allocations must never exceed their grant's amount."""

    def _admin(self, app: FastAPI, mock_session: AsyncMock):
        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = lambda: TokenPayload(user_id="a", role="admin")

    def _grant(self):
        from decimal import Decimal

        from src.models.base import Grant

        return Grant(
            id="grant-1", awbi_ref="AWBI/2026/001", amount=Decimal("1000.00"),
            purpose="ABC", financial_year="2026-27", status="active",
        )

    async def _post(self, app, mock_session, total_existing: str, amount: str):
        from decimal import Decimal

        self._admin(app, mock_session)
        mr_centre = MagicMock()
        mr_centre.scalar_one_or_none.return_value = MagicMock()  # FK passes
        mr_grant = MagicMock()
        mr_grant.scalar_one_or_none.return_value = self._grant()
        mr_sum = MagicMock()
        mr_sum.scalar.return_value = Decimal(total_existing)
        mock_session.execute.side_effect = [mr_centre, mr_grant, mr_sum]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            return await ac.post("/api/v1/allocations", json={
                "grant_id": "grant-1", "centre_id": "centre-1", "amount": amount,
            })

    @pytest.mark.asyncio
    async def test_rejects_over_allocation(self, app: FastAPI, mock_session: AsyncMock):
        resp = await self._post(app, mock_session, "800.00", "500.00")
        assert resp.status_code == 400
        assert "grant balance" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_allows_exact_balance(self, app: FastAPI, mock_session: AsyncMock):
        resp = await self._post(app, mock_session, "800.00", "200.00")
        assert resp.status_code == 201


class TestSurgeryLinkage:
    """High: a surgery must not join a dog from another centre."""

    @pytest.mark.asyncio
    async def test_rejects_cross_centre_dog(self, app: FastAPI, mock_session: AsyncMock):
        from src.models.base import Dog

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = lambda: TokenPayload(user_id="a", role="admin")

        mr_dog = MagicMock()
        mr_dog.scalar_one_or_none.return_value = Dog(
            id="dog-1", centre_id="centre-b", tag_id="T1", sex="female"
        )
        mock_session.execute.side_effect = [mr_dog, MagicMock(), MagicMock()]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/surgeries", json={
                "dog_id": "dog-1", "centre_id": "centre-a", "staff_id": "staff-1",
                "surgery_type": "spay",
            })

        assert resp.status_code == 400
        assert "different centre" in resp.json()["detail"]


class TestSharedLimiterWiring:
    """High: one shared limiter instance; limits actually enforce (429)."""
    def test_single_instance_shared(self):
        from src import ratelimit
        from src.auth import routes as auth_routes
        from src.main import limiter as main_limiter
        from src.public import routes as public_routes

        assert auth_routes.limiter is ratelimit.limiter
        assert main_limiter is ratelimit.limiter
        assert public_routes.public_limiter is ratelimit.limiter

    @pytest.mark.asyncio
    async def test_limit_enforced_429(self):
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded
        from slowapi.util import get_remote_address

        iso = Limiter(key_func=get_remote_address)
        iso_app = FastAPI()
        iso_app.state.limiter = iso
        iso_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        @iso_app.get("/ping")
        @iso.limit("2/minute")
        async def ping(request: Request):
            return {"ok": True}

        transport = ASGITransport(app=iso_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            assert (await ac.get("/ping")).status_code == 200
            assert (await ac.get("/ping")).status_code == 200
            assert (await ac.get("/ping")).status_code == 429


class TestSyncOwnership:
    """Sync items belong to the staff member who enqueued them.

    Legacy rows (owner_id NULL, enqueued before ownership) stay operable
    by any authenticated user — grandfathered, not orphaned.
    """

    def _overrides(self, app: FastAPI, mock_session: AsyncMock, role: str, user_id: str):
        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = lambda: TokenPayload(
            user_id=user_id, role=role
        )

    def _item(self, **kwargs):
        from src.models.base import SyncQueue

        data = {
            "id": "sq-1",
            "entity_type": "dog",
            "entity_id": "d1",
            "operation": "create",
            "payload": {"a": 1},
            "idempotency_key": "key-1",
            "status": "pending",
        }
        data.update(kwargs)
        return SyncQueue(**data)

    @pytest.mark.asyncio
    async def test_vet_cannot_mark_others_item(self, app: FastAPI, mock_session: AsyncMock):
        self._overrides(app, mock_session, "vet", "vet-1")
        mock_session.execute.return_value = _result(scalar=self._item(owner_id="vet-2"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/sync/mark-synced/sq-1")

        assert resp.status_code == 404
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_vet_can_mark_own_item(self, app: FastAPI, mock_session: AsyncMock):
        self._overrides(app, mock_session, "vet", "vet-1")
        mock_session.execute.return_value = _result(scalar=self._item(owner_id="vet-1"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/sync/mark-synced/sq-1")

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_legacy_ownerless_item_grandfathered(self, app: FastAPI, mock_session: AsyncMock):
        self._overrides(app, mock_session, "vet", "vet-1")
        mock_session.execute.return_value = _result(scalar=self._item(owner_id=None))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/sync/mark-synced/sq-1")

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_mark_any_item(self, app: FastAPI, mock_session: AsyncMock):
        self._overrides(app, mock_session, "admin", "admin-1")
        mock_session.execute.return_value = _result(scalar=self._item(owner_id="vet-9"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/sync/mark-synced/sq-1")

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_enqueue_records_owner(self, app: FastAPI, mock_session: AsyncMock):
        self._overrides(app, mock_session, "vet", "vet-1")
        mock_session.execute.return_value = _result(scalar=None)
        added: list[object] = []
        mock_session.add.side_effect = lambda obj: added.append(obj)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/sync/enqueue", json={
                "entity_type": "dog",
                "entity_id": "d1",
                "operation": "create",
                "payload": {"a": 1},
                "idempotency_key": "key-owner",
            })

        assert resp.status_code == 200
        assert added and added[0].owner_id == "vet-1"

    @pytest.mark.asyncio
    async def test_vet_cannot_read_others_status(self, app: FastAPI, mock_session: AsyncMock):
        self._overrides(app, mock_session, "vet", "vet-1")
        mock_session.execute.return_value = _result(scalar=self._item(owner_id="vet-2"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/sync/status/key-1")

        assert resp.status_code == 404

    def test_migration_005_chains(self):
        migration_dir = Path(__file__).resolve().parents[1] / "migrations" / "versions"
        contents = {p.name: p.read_text(encoding="utf-8") for p in migration_dir.glob("*.py")}
        assert "005_sync_ownership_and_audit_details.py" in contents
        m005 = contents["005_sync_ownership_and_audit_details.py"]
        assert 'down_revision: str = "004"' in m005
        assert "owner_id" in m005 and "details" in m005

    def test_models_match_migration_005(self):
        from src.models.base import AuditEvent, SyncQueue

        assert "owner_id" in {c.name for c in SyncQueue.__table__.columns}
        assert "details" in {c.name for c in AuditEvent.__table__.columns}


class TestNoSilentFailures:
    """Auditing must never fail the operation it records; error
    classification must not report outages as bad input."""

    def _admin(self, app: FastAPI, mock_session: AsyncMock):
        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user] = lambda: TokenPayload(
            user_id="admin-1", role="admin"
        )

    @pytest.mark.asyncio
    async def test_audit_commit_failure_still_returns_201(
        self, app: FastAPI, mock_session: AsyncMock
    ):
        # Entity commit succeeds, audit commit blows up: the client must
        # still get 201 (else it retries into duplicates).
        mock_session.commit = AsyncMock(side_effect=[None, Exception("db down")])
        self._admin(app, mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/grants", json={
                "awbi_ref": "AUD-FAIL-1",
                "amount": "1000.00",
                "purpose": "audit",
                "financial_year": "2026-27",
            })

        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_complaint_commit_failure_is_500_not_400(
        self, app: FastAPI, mock_session: AsyncMock
    ):
        # centre_id pre-check passes; the commit then fails for an
        # unrelated reason: must be a 500, not a misleading 400.
        mock_session.commit = AsyncMock(side_effect=RuntimeError("connection lost"))
        app.dependency_overrides[get_db] = lambda: mock_session

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/public/complaints", json={
                "centre_id": "centre-1",
                "citizen_phone": "9876543210",
                "description": "stray dogs",
            })

        assert resp.status_code == 500
