# ABC Compliance Platform — Codebase Audit Report

**Date:** 2026-08-15
**Scope:** Full-stack audit (FastAPI backend + React/TS frontend) via AEOS M10 (Product-Minded Engineer) → M23 (Comprehensive Auditor) + Ponytail over-engineering pass + correctness/security pass.
**Method:** Inventory → full source read (22 backend modules, key frontend modules) → pytest baseline → multi-dimensional assessment → triage.
**Baseline:** `77 passed, 4 skipped` (backend, **all DB access mocked** — no real query/migration paths exercised). Frontend: not built/run in this audit; static review only.

---

## Executive Summary

The platform is a clean, modular FastAPI + React application for Animal Birth Control (ABC) centre compliance. Structure is good: routers split by domain, consistent Pydantic request/response models, bcrypt + JWT auth, security headers middleware, non-root Docker user, correlation-ID middleware, and a real CI pipeline (pytest + ruff + pyright + oxlint + impeccable + vitest + playwright). Recent commits show active hardening (IDOR fix on notifications, inactive-login rejection, password-hash exposure fix).

The headline problem is **authorization depth**: authentication exists, but endpoints have almost no *object-level* authorization (RBAC is role-only; no ownership/centre scoping). Any authenticated `vet`/`surgeon` can read or mutate any centre, dog, surgery, inspection, complaint, or sync item by guessing its UUID. For a multi-tenant government compliance system holding citizen complaints and fund data, that is a blocking P0.

Secondary P0s: refresh tokens are never revoked (logout is cosmetic, `jti` is generated but never blacklisted, so a stolen/refresh token survives password change and deactivation until its 7-day expiry), and the **audit trail is not wired** — `log_audit_event()` exists but no mutation calls it, defeating the platform's core compliance promise.

Test coverage is broad but shallow: every test mocks the DB session, so the actual SQLAlchemy queries, the 7 committee models, and the Alembic migrations are never run. Several frontend pages (CommitteePortal) are mock-only with no backend, and `api.getDogs` is a hard no-op stub.

**Overall health: 6/10.** Deployable for a demo; not safe to put real citizen/fund data in without fixing the P0 authorization and audit-trail gaps.

---

## Module Inventory (AEOS 26-module mapping)

| AEOS Module | Status | Note |
|---|---|---|
| 1 Constitution | PARTIAL | pyproject + AGPL headers; no explicit engineering principles doc |
| 4 Engineering Memory | MISSING | No tracking doc in repo |
| 9 Architect | DONE | Clean router-per-domain split |
| 10 Product-Minded | DONE (this report) | See bottlenecks below |
| 12 UI/UX | DONE | M3 Material theme, lazy routes, premium UI |
| 13 Dependency Audit | PARTIAL | `passlib`, `python-multipart` likely unused (see ponytail) |
| 14 TDD | PARTIAL | Tests exist but DB fully mocked |
| 15 Logic Review | PARTIAL | Expense race, refresh-retry dead branch (see findings) |
| 16 Code Review | DONE (this report) | See concerns |
| 17 Debugging | N/A | No active incident |
| 18 QA | MISSING | No e2e/playwright run in audit; pages untested |
| 19 Security | PARTIAL | Auth solid; authz/IDOR gaps (P0) |
| 20 Performance | PARTIAL | In-memory cache per-process; no N+1 issues spotted |
| 21 Cleanup | DONE (this report) | Dead code flagged |
| 22 Tech Writer | PARTIAL | README exists; version strings stale |
| 23 Auditor | DONE | This report |
| 24 Release/DevOps | DONE | Dockerfile + CI + compose good |

---

## Top 10 Highest-Risk Issues (ranked by production impact)

### P0-1 — Object-level authorization missing (horizontal IDOR) — SECURITY
**Location:** `src/centres/routes.py`, `src/dogs/routes.py`, `src/surgeries/routes.py`, `src/inspections/routes.py`, `src/public/routes.py`, `src/funds/routes.py`
**Root cause:** Endpoints gate on `require_role(...)` only. No `centre_id`/ownership check against the calling user's `TokenPayload`. A `vet` at centre A can `GET /centres/{id}` for centre B, `PATCH /public/complaints/{id}` for any centre's complaint, `POST /surgeries` for another centre, read another centre's `sync` queue (`/sync/pending` is `get_current_user` only — returns ALL centres' pending items to any staff).
**Impact:** Any authenticated low-privilege user reads/writes every other centre's animals, surgeries, inspections, citizen complaints, and fund allocation data. For a government compliance platform this is a confidentiality and data-integrity breach.
**Note:** Notifications routes *do* scope correctly (`get_notification` checks `user_id`/admin) — that fix was already applied; replicate the same pattern everywhere.
**Fix:** Add a dependency that resolves the caller's `centre_id` (from `Staff.centre_id`) and enforce it on every entity read/write; or introduce a `require_centre_access(centre_id)` guard. At minimum, scope list endpoints by caller centre for non-admins.

### P0-2 — Refresh tokens never revoked; logout is cosmetic — SECURITY
**Location:** `src/auth/deps.py` (`create_refresh_token` generates `jti`, never stored), `src/auth/routes.py` (`/logout`, `/refresh`, `/delete_account`)
**Root cause:** `jti` is created but there is no denylist/DB store. `logout` only clears client cookies; the refresh token remains valid for 7 days. `delete_account` deletes the staff row but issued tokens still validate until expiry. Password change (future) wouldn't invalidate sessions.
**Impact:** A stolen refresh token (or a token on a shared/lost device) grants access for up to 7 days after "logout"; a deactivated account keeps working until token expiry.
**Fix:** Persist refresh-token `jti` (or a `revoked` flag / token version on `Staff`) and check it in `verify_refresh_token` and/or `decode_token`. On logout/delete/deactivate, revoke. Cheapest: add `token_version` int column to `Staff`, bump on password change/deactivate, embed in JWT, reject on mismatch.

### P0-3 — Audit trail not wired into mutations — COMPLIANCE
**Location:** `src/audit/routes.py` (`log_audit_event` defined) — never called by any route; `AuditEvent` model has no `details` column despite `AuditEventCreate.details`.
**Root cause:** The audit logger is implemented but no write path invokes it. Mutations (create/update/delete on centres, surgeries, inspections, complaints, funds, sync) leave no audit row.
**Impact:** The platform's core value (tamper-evident compliance log) does not function. Also `audit_hash`/`signoff_hash` columns on `Surgery`/`Inspection` are never populated.
**Fix:** Call `log_audit_event(db, entity_type, entity_id, action, actor_id=user.user_id)` inside each mutation; add a `details` JSONB column to `AuditEvent`; populate `audit_hash` on surgery/inspection write (or drop the unused columns).

### P0-4 — Expense over-allocation race (read-modify-write, no lock) — CORRECTNESS/FINANCE
**Location:** `src/funds/routes.py` `create_expense` (lines 159-180)
**Root cause:** Balance is computed as `sum(existing) + body.amount` in two queries, then compared. Two concurrent `create_expense` calls for the same allocation both read the same sum and both commit → total can exceed `allocation.amount`.
**Impact:** Fund allocations can be overspent silently — a real financial-control failure.
**Fix:** Enforce the ceiling in SQL (`UPDATE allocations SET ...` with a CHECK, or `SELECT ... FOR UPDATE` inside the transaction, or compute remaining server-side with a row lock). Add a test with concurrent inserts.

### P0-5 — `/auth/me` contract mismatch breaks profile UI — CORRECTNESS
**Location:** `src/auth/routes.py` `me` returns `TokenPayload {user_id, role}`; frontend `types/index.ts` `User` expects `{user_id, name, phone, centre_id}`; `AuthContext.fetchUser` sets `user` from it.
**Root cause:** Backend never returns `name`/`phone`/`centre_id` (they aren't in the JWT beyond `sub`/`role`). Frontend `user.name`, `user.phone`, `user.centre_id` are always `undefined`.
**Impact:** Profile page, personalization, and any centre-scoped UI show empty/undefined values. Silent — tests mock the user.
**Fix:** Either embed `name`/`phone`/`centre_id` in the access token at login, or have `/auth/me` query `Staff` and return the full profile. Align the `User` type to the actual response.

---

## P1 — Should Fix

### P1-1 — `api.getDogs` is a hard no-op stub — CORRECTNESS
**Location:** `frontend/src/services/api/index.ts` lines 51-53 (`getDogs: () => Promise.resolve([])`)
**Impact:** Any UI using dogs silently shows nothing and looks broken. Either wire to `src/dogs/routes.py` (which exists and works) or remove the dead export.

### P1-2 — CommitteePortal is mock-only; 7 backend models orphaned — WASTE/DRIFT
**Location:** `frontend/src/pages/CommitteePortal.tsx` (no `api.` calls, no `fetch`); `src/models/base.py` `Committee`/`Meeting`/`Decision`/`Vote`/`CommitteeMember`/`MeetingAttendee`/`CommitteeDocument` — unreferenced by any router; **no Alembic migration creates these tables.**
**Impact:** ~120 lines of models + a 350-line page reference data that never exists. If a migration is later added, the tables appear but have no API. Confusing surface for contributors.
**Fix:** Decide: (a) build the committee routers + migration + wire the page, or (b) delete the models and the page now. Don't ship dead surface.

### P1-3 — `FundRequestModal` submit is a TODO — INCOMPLETE FEATURE
**Location:** `frontend/src/pages/FundTracker.tsx` line 407-409 (`console.log('Submitting fund request:', data)`)
**Impact:** "New Fund Request" button does nothing. Either implement or hide until backed.

### P1-4 — Report options ignored (decorative) — FEATURE GAP
**Location:** `src/reports/routes.py` `generate_report`: `format` (json/excel/pdf) is accepted but only JSON is ever returned; `highlight_critical`/`compare_benchmark`/`include_sub_entities` are echoed back but not used in computation.
**Impact:** Report UI implies capabilities that don't exist. Misleads users.
**Fix:** Implement or strip the unused request fields; document the actual output.

### P1-5 — `console.log`/`console.error` in frontend — OBSERVABILITY/HYGIENE
**Location:** `FundTracker.tsx` (3× `console.log('View All clicked')`, `console.log('Submitting...')`), `Surgeries.tsx`, plus many `console.error` in catch blocks.
**Impact:** Dev noise in production; not a leak, but `console.error` in every catch is noise. Gate or remove the `console.log` debug lines; keep structured errors.

### P1-6 — Stale version strings — PONytail/DOCS
**Location:** `src/main.py` `app = FastAPI(..., version="0.1.0")`, `lifespan` logs `"0.1.0"`; `pyproject.toml` `version = "0.1.0"`; `CHANGELOG.md` is at `0.4.0`.
**Impact:** /docs and health report the wrong version; contributors can't trust the changelog-to-code mapping.
**Fix:** Single source of truth (read from package metadata) or bump all three.

### P1-7 — `/health` reports `redis: True` hardcoded — OBSERVABILITY
**Location:** `src/main.py` `health` — `checks["redis"] = True` is a literal; no Redis is used (cache is in-memory).
**Impact:** Health signal is misleading; if Redis is ever added, the check won't detect downtime.
**Fix:** Drop the redis check or actually ping it.

---

## P2 — Nice to Have

- **Self-service `vet` registration (no admin gate):** `register` always creates `role="vet"` from a public endpoint (rate-limited 3/hr). For a gov platform, consider admin-approved onboarding. (Design decision — flag, don't block.)
- **`sync` queue is write-only:** `enqueue`/`mark-synced`/`retry` exist but nothing *consumes* the queue to actually sync offline data back. It's a backlog with no processor. Confirm intent.
- **`create_expense` only checks allocation balance, not grant balance:** nested over-spend possible if multiple allocations draw from one grant.
- **`register` error handling keys off `str(e).lower()` substrings** (`"phone"`, `"unique"`) — brittle but works; acceptable.
- **CI installs from `requirements.txt` with hardcoded path** `/home/runner/work/ABC-Compliance-Platform/ABC-Compliance-Platform` — fragile if repo renamed. Use `${{ github.workspace }}`.

---

## Ponytail Bloat Pass (dead code / over-engineering)

- `delete:` `src/cache.py` — `cached()` decorator and `invalidate_cache()` are never used (only `cache`, `cache_key`, `invalidate_pattern` are). Remove the dead decorator + function.
- `delete:` `src/config.py` — `redis_url` setting is never read anywhere (cache is in-memory). Remove unless Redis is planned.
- `yagni:` `src/main.py` — three separate `Limiter` instances (main, auth, public routers) each with own in-memory storage. Consolidate to one shared limiter to avoid duplicate state and confusion.
- `delete:` `passlib[bcrypt]` and `python-multipart` in `pyproject.toml`/`requirements.txt` — code uses `bcrypt` directly and JSON bodies (no `Form`); both appear unused. Verify and drop if so.
- `shrink:` `src/reports/routes.py` — repetitive per-template `from src.models.base import ...` imports inside each branch; hoist to top.
- `delete:` `AuditEventCreate.details` field has no backing column — remove or add the column.

**net: ~ -60 lines, -2 deps possible** (pending verification of `passlib`/`python-multipart` usage in the venv).

---

## Security Hardening Checklist

- [x] bcrypt password hashing
- [x] JWT HS256 with 32-byte minimum key enforced
- [x] Security headers middleware (HSTS, X-Frame-Options, CSP, Referrer-Policy)
- [x] CORS credentials scoped to `allowed_origins` (no wildcard)
- [x] Correlation-ID + global exception handler (no stack traces leaked)
- [x] Notifications IDOR fixed (ownership check)
- [ ] **Object-level authz on all entity endpoints (P0-1)**
- [ ] **Refresh-token revocation (P0-2)**
- [ ] **Audit trail wired (P0-3)**
- [ ] Rate-limit verified at runtime on auth endpoints (3 Limiter instances — likely works but untested)
- [ ] SQL injection: parameterized via SQLAlchemy ORM throughout (no raw string SQL found) ✓
- [ ] XSS: no `dangerouslySetInnerHTML` / `innerHTML` in frontend ✓

---

## Testing Strategy Improvements

- **Real-DB integration tests:** current 77 tests all mock `get_db` with `AsyncMock`. Add a SQLite/Postgres integration suite (the skipped `test_integration.py` already requires `DATABASE_URL`) that exercises real queries, the expense-balance lock, and ownership scoping.
- **Authz tests:** add negative tests proving a `vet` at centre A CANNOT read/write centre B (would catch P0-1).
- **Audit tests:** assert a mutation creates an `AuditEvent` row.
- **Frontend:** run the existing Playwright suite; cover `AuthContext` token refresh (currently the retry branch is dead — see P0-5-adjacent note below).

---

## Production Readiness Score: 6/10
## Architecture: 7/10 · Security: 5/10 · Correctness: 6/10 · Maintainability: 7/10 · Testing: 6/10 · Frontend: 6/10

---

## Immediate Quick Wins (each < 30 min)
1. Fix `/auth/me` to return full profile (P0-5) — unblocks Profile UI.
2. Remove `api.getDogs` stub or wire it (P1-1).
3. Delete dead `cached()`/`invalidate_cache()`/`redis_url` (Ponytail).
4. Fix `/health` redis check (P1-7).
5. Bump version strings to 0.4.0 (P1-6).

## High-Impact Refactors (must precede real data)
1. Object-level authorization dependency across all entity routers (P0-1).
2. Refresh-token revocation via `token_version` column (P0-2).
3. Wire `log_audit_event` into every mutation (P0-3).
4. Lock/expense-balance enforcement in SQL (P0-4).
5. Resolve CommitteePortal: build or delete (P1-2).
