# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Compliance Heatmap** — India choropleth on the Reports page showing compliance rate and risk level per state, based on real AWBI-recognised ABC centre data
- **AWBI Centre Data** — Seed script (`scripts/seed_awbi_centres.py`) that loads 66 real AWBI-recognised centres from the official list into the database
- **State-level aggregation endpoint** — `GET /api/v1/public/heatmap` returns centres, inspections, compliance rate and risk per state

### Fixed
- **Dashboard centre count** — now requests up to 100 centres so the total reflects all registered centres, not just the first 50

## [0.2.0] - 2026-08-01

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