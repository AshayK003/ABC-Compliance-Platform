# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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