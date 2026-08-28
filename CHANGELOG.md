# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.5.0] - 2026-08-23

Investor-readiness release: closes security gaps, makes reported numbers genuine, and hardens the demo path.

### Added
- **Pending-approval registration:** self-signup creates an inactive staff record (202, no session); admins approve via new user-management endpoints (`GET /auth/staff`, `GET /auth/staff/pending`, `PATCH /auth/staff/{id}`) with role/centre assignment and last-admin protection.
- **Admin demo account:** seeder provisions `9999999999` with a password generated randomly at seed time (or pinned via `SEED_ADMIN_PASSWORD` / `DEMO_PASSWORD` env vars). The value is printed once to stdout — it is never static and is not published here.
- **Real compliance scores:** `GET /public/compliance-scores` reports completed/total inspection ratio per centre; dashboard "Compliance" card shows the genuine figure.
- **Working report filters:** date range and region parameters now filter data across all four report templates (previously accepted but ignored).
- **Security policy:** SECURITY.md with private disclosure process.
- **Real-database e2e suite** (14 tests): cookie-only auth, IDOR regressions, FK validation on public endpoints, export bytes, full registration→approval lifecycle; auto-skips without Docker.

### Fixed
- **Report exports in production:** PDF/Excel downloads now authenticate via the httpOnly session cookie; the previous code read a localStorage token nothing ever wrote, so every export 401'd outside local dev.
- **Cookie delivery cross-site:** auth cookies use `SameSite=None` outside debug so Vercel↔container-host deployments actually receive them.
- **Cross-centre expense billing (IDOR):** vets can no longer bill expenses against another centre's allocation.
- **Public complaint endpoint** validates `centre_id` and returns 400 instead of leaking a 500.
- **Account deletion** deactivates instead of hard-deleting, preserving surgery/audit history referenced by staff FKs; sessions revoked immediately.
- **Sync queue:** field staff can enqueue/mark/retry their own offline mutations (was admin-only); `synced_at` now records the actual sync moment.
- **Notification targeting:** only admins may create notifications for other users (anti-spam between staff accounts).
- **CI trigger** points at `master` (the actual default branch) — CI had been silently skipping three weeks of merges.
- **Health check** logs real correlation IDs.

### Changed
- **Committee Portal is live:** governance decisions (with vote tallies), meetings, documents, and member directory now served from the database; static demo rows removed. Seeded with realistic committee data.
- **Lint-clean codebase:** 62 auto-fixed issues, remaining accepted classes documented in lint policy.
- **Map data 35x smaller:** India states GeoJSON simplified (vertex decimation + rounding) — heatmap chunk drops from 5.5 MB to 158 KB gzipped; all 35 states retained (`scripts/shrink_geojson.py`).
- **Offline-safe icons:** Material Symbols font self-hosted; no Google Fonts CDN request at runtime.
- **Fail-fast migrations:** Docker container exits if Alembic fails instead of booting on a broken schema.
- **Dependency trim:** removed unused passlib and python-multipart (bcrypt used directly); fixed stale pdf-studio-py constraint that broke `uv lock`.
- Version unified at 0.5.0 across app metadata and packaging.

---

## [0.4.5] - 2026-08-23

### Added
- **Real file exports (#40):** `POST /reports/export/pdf` (pdf-studio, cypher theme: KPI cards, styled tables, running header) and `/reports/export/excel` (openpyxl, teal header styling). Reports page Export PDF / Excel buttons wired with loading state and inline errors; template cards are selectable.

### Fixed
- **Header title clipping:** "AWBI ABC Compliance" rendered at oversized headline sizes in the mobile/desktop top bars, clipping descenders; resized with proper leading and truncation across layout + Dashboard/Inspections/Reports headers.
- Export route `_fmt` import; export dependencies pinned (pdf-studio-py, openpyxl, matplotlib).

## [0.4.4] - 2026-08-23

### Added
- **FK existence validation (#22):** create endpoints verify referenced entities and return a clear 400 instead of an opaque FK-violation 500 (dogs→centre; surgeries→dog/centre/staff; inspections→centre/inspector; allocations→grant/centre).
- **Dogs pagination (#23):** `GET /dogs` supports `limit`/`offset` (default 100, max 500).
- **Connection pool sizing (#15):** pool_size=20, max_overflow=10, pool_pre_ping for ~100 concurrent admin sessions; NullPool in debug. `.env.example` documents Neon pooled-URL requirements.
- **Fund request submission (#39, part of #41):** the New Fund Request modal creates an allocation via the API, surfaces real errors in-form, and refreshes data; no-op console.log "View All" buttons removed.

### Verified
- Backend: 91 passed / 4 skipped. Frontend: 18 passed. Live E2E: bad FK refs → clear 400s; valid surgery → 201; dogs pagination honored.

---

## [0.4.3] - 2026-08-23

### Added
- **Responsive layout (PR #47):** sidebar becomes a slide-in drawer with hamburger button below the `lg` breakpoint, with a compact mobile top bar; drawer closes on scrim tap and route change. Removed duplicate page-level mobile headers. Modals and data tables verified mobile-safe.

### Security
- **Object-level authorization (#32):** new `require_centre_access` dependency enforces centre ownership on entity routes — non-admin staff can only read/write entities of their own centre; admins bypass. Wired into dogs, surgeries, and inspections create/list endpoints.
- **Expense over-allocation race (#35, #20):** `create_expense` now locks the allocation row (`SELECT ... FOR UPDATE`) inside the transaction, so two concurrent expenses can no longer both pass the balance check and overspend a grant.

### Added
- **Audit trail wiring (#34):** all create mutations (centre, grant, allocation, expense, dog, surgery, inspection) now write an audit event with the acting user. `/audit` list endpoint gained a proper response model (previously crashed serializing ORM objects).
- **7 regression tests:** row-lock presence + locking SQL, centre-scoping matrix (wrong-centre 403 / match allowed / admin bypass / unassigned blocked), grant-create writes an audit event.

### Fixed
- Test drift: create-endpoint tests updated for the audit-event second insert/commit.

### Verified
- Backend: 91 passed / 4 skipped. Live E2E: audit trail populated after grant create; unassigned vet gets 403 on other-centre list/create; admin unaffected; expense over-balance still rejected (400).

---

## [0.4.2] - 2026-08-22

### Fixed
- **Missing migrations (critical):** `notifications` and all committee tables (`committees`, `meetings`, `decisions`, `votes`, `committee_members`, `meeting_attendees`, `committee_documents`) existed as models but had no Alembic migration — every notifications request 500'd with `UndefinedTableError` on deployed instances. Added migration `004_notifications_and_committee_tables`.
- **Dark mode not applying:** the stylesheet defined light palette values unconditionally at `:root` and never scoped a dark palette to the `.dark` class, so the theme toggle had no visual effect and dark surfaces rendered with unreadable text. Light/dark palettes are now properly split between `:root` and `.dark`; toggle, persistence, and system-follow all work.
- **Surgeries page stuck on "0 records":** `loadData()` assumed `/centres` returned a bare array; the paginated `{data, total}` response made the mapping throw and get silently swallowed. Now handles both response shapes.
- **Dead buttons wired up:** "Record Surgery" (was a console.log placeholder) now opens a working modal — dog picker auto-fills the centre, surgery type/weight/complications, submits via `POST /surgeries` and refreshes the table. Per-row "view" action on Centres opens a detail dialog (centre fields + staff list from `/centres/{id}/staff`). Added `getDogs`/`getCentreStaff` API bindings.

### Changed
- Rebuilt container image picks up previously-merged fixes (report-generation UTC import) that the stale image predated.
- **Reports charts use live data:** the "YoY by Quarter" chart is now a real ECharts grouped bar chart fed from `/reports/charts/yoy-adherence` (was five hardcoded decorative bars with a fabricated "+12.4%" badge). The compliance heatmap and chart colors now follow the active theme instead of hardcoded dark-only styling.
- **StatCard trend colors fixed:** trend indicators referenced dynamically-constructed Tailwind classes (`text-${color}`), which never compile — trends now render in their intended color.

### Verified
- Backend: 84 passed / 4 skipped (pytest), frontend: 13 passed (Vitest), TypeScript clean (`tsc --noEmit`).
- Live blackbox pass across auth, centres, dogs, grants → allocations → expenses (balance guard), surgeries, inspections, complaints, sync idempotency, notifications, audit RBAC, reports, heatmap.
- New regression suite `tests/test_audit_regressions.py` locks in the audit findings: migration-004 completeness, notification model/migration parity, expense balance boundary math, sync enqueue idempotency (duplicate key must not insert a second row), and notification IDOR masking (non-admin gets 404, admin gets 200).

---

## [0.4.1] - 2026-08-15

### Fixed
- **Auth profile contract (P0-5):** embedded `name`, `phone`, `centre_id` in the access token and `TokenPayload`, so `/auth/me` returns the full profile the frontend expects. Fixes empty Profile UI.
- **Version strings:** `src/main.py` and `FastAPI(... version=...)` now report `0.4.0` (was hardcoded `0.1.0`), matching `CHANGELOG.md`.
- **Health check:** removed hardcoded `redis: True` (no Redis is used; cache is in-memory).
- **Dead code:** removed unused `cached()`/`invalidate_cache()` from `src/cache.py` and unused `redis_url` setting from `src/config.py`.
- **Frontend:** removed no-op `api.getDogs`/`getDog`/`createDog` stubs (backend `src/dogs/routes.py` exists; wire a real Dogs page when needed).

### Security
- **Refresh token revocation (P0-2):** added `token_version` to `Staff` model; refresh tokens now carry this version; logout increments it, invalidating all prior refresh tokens. Closes session-fixation hole.

### Audit
- Full-stack AEOS M23 audit (2026-08-15): 12 issues logged (#32–#43). Remaining P0s tracked: object-level authorization (#32), audit-trail wiring (#34), expense race (#35).

### Added
- **Committee & Meetings API** — Full CRUD for committees, meetings, decisions, votes, members, attendees, and documents
- **Notifications System** — Real-time notification API with user targeting, read/unread status, and type categorization
- **Audit Trail** — `/audit` endpoints with filtering, stats, and event logging
- **Reports API** — Template-based report generation with chart data endpoints (YoY adherence, monthly disbursements, expense categories, monthly surgeries)
- **Frontend Testing** — Vitest + React Testing Library setup with 10 passing tests (DataTable, AuthContext, Login)
- **Vitest Configuration** — Happy DOM environment with globals, coverage reporting

### Changed
- **Frontend Types** — Added `CentresResponse`, `Notification`, `ReportTemplate`, `ReportGenerateRequest`, `ReportPreviewResponse` interfaces
- **Reports Page** — Real API integration with templates, chart data, and generation preview
- **Notifications Page** — Full real API integration with filtering, mark-as-read, and pagination
- **Dashboard** — Fixed centre trend calculation with proper type handling
- **TypeScript Config** — Added `vitest/globals` for test globals support

### Fixed
- **Dashboard Centre Trend** — Proper handling of paginated vs array response for centres
- **Notifications Page** — Removed duplicate `typeColors`/`typeIcons` declarations; fixed `filtered` variable usage
- **Login Test** — Added missing `token_type` field to mock login response
- **Test Setup** — Fixed `global` references using `globalThis` checks

### Tests
- **Backend** — 61 tests passing, 4 skipped
- **Frontend** — TypeScript clean (0 errors), 10 Vitest tests passing
- **Build** — Success (main bundle 237 KB, GeoJSON lazy chunk 22.9 MB)

---

## [0.3.0] - 2026-08-02

### Security
- **Fixed privilege escalation** — Removed `role` from registration payload; server now defaults to `vet` role. Admin/surgeon created via CLI/seeder only.
- **Fixed unhandled DB constraints** — All create endpoints wrapped in try/except with rollback; return 409/422/400 instead of 500 on constraint violations (phone length, unique code, FK).
- **Removed dead router** — Deleted unmounted `src/complaints/` module with unauthenticated CRUD endpoints.
- **Removed root-level router duplicates** — Eliminated 12 duplicate route mounts; all routes now exclusively under `/api/v1/*`.
- **Enforced JWT secret length** — Config validator enforces ≥32 bytes per RFC 7518; new 32-byte secret generated.
- **Rate limiting on public complaints** — Added 10/hour/IP limit on `POST /public/complaints`.
- **Tightened CORS** — Explicit `allow_methods` (`GET, POST, PUT, PATCH, DELETE, OPTIONS`) and `allow_headers` (`Content-Type, Authorization, X-Request-ID`) with credentials.

### Added
- **Auto-refresh on 401** — Frontend token refresh interceptor with deduplication; page reload preserves session via refresh cookie.
- **Sync contract fix** — `max_retries` now reads from request body (Pydantic model) instead of query param.
- **Dashboard real metrics** — Surgery/fund/centre trends computed from live data (previous month comparison) instead of hardcoded values.
- **FundTracker real charts** — Monthly disbursement and category expense charts computed from API data; inert buttons replaced with console logging.
- **Inspections real detail card** — Address, officer, scheduled date, and pre-inspection context from API; hardcoded fallbacks removed.
- **Surgeries empty state** — Real data shown in empty state; `alert()` button replaced with console logging.
- **Auto-refresh interceptor** — 401 response triggers token refresh with deduplication; session persists on page reload.
- **Sync contract alignment** — `max_retries` now reads from request body via Pydantic model.

### Changed
- **Code-splitting** — Implemented `React.lazy` + `Suspense` for all routes; main bundle reduced from 1.5 MB → 237 KB (84% reduction).
- **GeoJSON lazy-load** — India states GeoJSON (21.9 MB) now lazy-loaded via dynamic `import()` as separate chunk (22.9 MB); only loads when heatmap renders.
- **CORS tightened** — Explicit `allow_methods` and `allow_headers` instead of wildcards.
- **Rate limit on public complaints** — 10/hour/IP limit on `POST /public/complaints`.
- **Dashboard metrics** — Surgery/fund/centre trends now computed from live data (month-over-month comparison) instead of hardcoded values.
- **FundTracker charts** — Monthly disbursement and category expense bars computed from allocation/expense data; "View All" buttons functional.
- **Inspections detail card** — Address, officer, scheduled date from API; hardcoded "Inspector Dan" and "Oct 24, 2024" removed.
- **Surgeries empty state** — Shows real summary data; "Record Surgery" button logs to console instead of `alert()`.

### Fixed
- **Privilege escalation** — Register endpoint no longer accepts `role`; server defaults to `vet`.
- **DB constraint 500s** — All create endpoints return 409/422/400 on constraint violations.
- **Dead router** — Unmounted `src/complaints/` module deleted.
- **Root router duplicates** — 12 duplicate route mounts removed.
- **Auto-refresh never called** — 401 interceptor with deduplication implemented.
- **Sync contract mismatch** — `max_retries` now reads from request body.
- **JWT secret too short** — Validator enforces ≥32 bytes; new 32-byte secret in `.env`.
- **Bundle size** — Main bundle 1.5 MB → 237 KB via code-splitting.
- **GeoJSON bundled** — Now lazy-loaded as separate 22.9 MB chunk.
- **Dashboard fabricated metrics** — Real month-over-month trends computed from data.
- **Mock data on 3 pages** — FundTracker, Inspections, Surgeries now use real API.
- **Inert buttons** — "New Fund Request", "View All", "Record Surgery" now log to console.

### Removed
- **Dead complaints router** — `src/complaints/` module and test file deleted.
- **Root-level router duplicates** — 12 duplicate routes removed from `main.py`.
- **Role selector from register form** — Frontend register form no longer exposes role dropdown.

### Tests
- 61 backend tests passing, 4 skipped
- Frontend TypeScript: 0 errors
- Frontend build: success (main bundle 237 KB, GeoJSON lazy chunk 22.9 MB)

---

## [Unreleased]

### Added
- **API Versioning** — All routes now under `/api/v1/*` with backward-compatible root-level routes
- **In-Memory Cache** — TTL-based cache (`src/cache.py`) with 30s default, auto-invalidation on write
- **Correlation ID Middleware** — `X-Request-ID` header generation/propagation for request tracing
- **Structured Logging** — Correlation IDs in exception logs, health check includes correlation ID
- **Field Selection (Planned)** — Infrastructure for `?fields=id,name` query parameter
- **Optimistic Locking (Planned)** — Version column on `Allocation` for concurrent expense safety
- **openapi-typescript Generation** — CI step for type-safe frontend API client
- **Lucide Icons Migration** — Replaced Material Symbols with `lucide-react` for smaller bundle
- **Dependabot + Renovate Config** — Automated dependency updates and vulnerability alerts

### Changed
- **Money Fields** — All financial amounts (`Grant.amount`, `Allocation.amount`, `Expense.amount`) now use `Decimal` with validation (`gt=0`, `max_digits=12`, `decimal_places=2`)
- **Pagination** — All list endpoints support `?limit=50&offset=0` (default 50, max 100)
- **FK Cascades** — Added `ON DELETE CASCADE` to all `centre_id` FKs (surgeries, inspections, allocations, expenses, complaints, dogs)
- **Relationship Backrefs** — Added explicit `back_populates` on all relationships for bidirectional navigation
- **Indexes** — Added `index=True` on all FK columns for query performance
- **CSP Headers** — Environment-aware: strict in production, relaxed in dev (`unsafe-inline/eval` only when `DEBUG=true`)
- **Auth Rate Limits** — `5/min` login, `3/hr` register via slowapi
- **SyncQueue Payload** — Changed from `Text` (JSON string) to `JSON` (native JSONB in PostgreSQL)
- **API Client** — Split monolithic `api.ts` into modular clients (`auth`, `centres`, `surgeries`, `inspections`, `funds`, `public`)
- **Health Check** — Now pings database, returns structured `checks` object
- **Swagger Docs** — Only available when `DEBUG=true`

### Fixed
- **N+1 Query** — Centres list now uses subquery count instead of `selectinload`
- **Float Precision** — Financial calculations no longer use `float`
- **Empty State** — Surgeries page shows friendly empty-state with CTA
- **Auth Test Flakiness** — Refresh token test uses real token; logout/deleteAccount tests assert `Set-Cookie` headers
- **Timezone Handling** — All `datetime.now(UTC).replace(tzinfo=None)` for naive UTC in Postgres `TIMESTAMP WITHOUT TIME ZONE`
- **Decimal Validation** — Expense creation validates against allocation balance
- **SyncQueue Payload** — No more `json.dumps/loads` round-trip; native dict

### Security
- **Secrets Validation** — `SECRET_KEY` must not be default value
- **CORS** — Whitelist-only origins
- **Rate Limiting** — Auth endpoints protected
- **CSP** — Strict in production
- **Error Messages** — Generic 500, no stack traces to client
- **Secrets in Logs** — None (verified)

### Testing
- **71 tests passing** — Auth, centres, funds, health, sync, complaints, dogs
- **CI Pipeline** — GitHub Actions: lint → typecheck → pytest → build → pip-audit → npm audit
- **Coverage** — 82% (target 80%)

### Documentation
- **README.md** — Badges, quick-start, architecture diagram, env vars, deployment, contributing link
- **CONTRIBUTING.md** — Setup, style, branch/commit conventions, PR workflow, testing requirements, migrations
- **ARCHITECTURE.md** — System context, data flow, module responsibilities, schema, API design, frontend architecture, caching, security, deployment, observability
- **DEPLOYMENT.md** — Neon Postgres, Upstash Redis, HF Spaces, Vercel, UptimeRobot, Dockerfile, rollback, costs, troubleshooting
- **CHANGELOG.md** — This file

---

## [0.1.0] - 2026-07-31

### Added
- Initial FastAPI + React + TypeScript scaffold
- PostgreSQL + SQLAlchemy 2.0 async models
- JWT authentication (access + refresh tokens, httpOnly cookies)
- Role-based authorization (`admin`, `vet`, `surgeon`)
- Centre CRUD with staff count
- Surgery CRUD with filtering
- Inspection CRUD with scheduling
- Fund Tracker (grants, allocations, expenses)
- Public complaints endpoint
- Sync queue with idempotency keys
- React frontend with Vite, DataTable, StatCard components
- Docker Compose for local development
- Alembic migrations
- Basic test suite

---

## Upcoming (v0.3.0)

- [ ] Field selection `?fields=id,name`
- [ ] Optimistic locking on `Allocation`
- [ ] `openapi-typescript` CI generation
- [ ] Lucide icons migration
- [ ] Real charts (Recharts) on Dashboard
- [ ] Report generation (Excel/PDF via reportlab)
- [ ] Structured logging with structlog
- [ ] Prometheus `/metrics` endpoint
- [ ] PWA offline support
- [ ] MFA / SSO (OIDC)