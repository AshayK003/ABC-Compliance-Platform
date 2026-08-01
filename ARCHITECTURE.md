# Architecture Overview

## System Context

The ABC Compliance Platform is a **civic-tech** application serving **Animal Welfare Board of India (AWBI)** and **State Animal Welfare Boards** to digitize compliance for **Animal Birth Control (ABC)** centres.

### Stakeholders
| Role | Access | Use Case |
|------|--------|----------|
| **Centre Vet/Surgeon** | Authenticated (vet/surgeon) | Log surgeries, view centre data |
| **Centre Admin** | Authenticated (admin) | Manage centre, staff, view compliance |
| **State Board Official** | Authenticated (admin) | Schedule inspections, monitor funds, generate reports |
| **AWBI Central** | Authenticated (admin) | Pan-state oversight, fund allocation, policy compliance |
| **Citizen** | Public (no auth) | Submit complaints via public endpoint |

---

## High-Level Data Flow

```
┌─────────────┐     HTTPS /api/v1      ┌─────────────┐
│   React     │ ─────────────────────▶ │  FastAPI    │
│  (SPA)      │ ◀───────────────────── │  (REST)     │
└─────────────┘       JSON              └──────┬──────┘
                                                 │
                    ┌───────────────────────────┼───────────────────────────┐
                    ▼                           ▼                           ▼
            ┌───────────────┐           ┌───────────────┐           ┌───────────────┐
            │  PostgreSQL   │           │     Redis     │           │  File System  │
            │  (Primary)    │           │  (Cache/Rate  │           │  (Exports,    │
            │               │           │   Limit/Queue)│           │   Reports)    │
            └───────────────┘           └───────────────┘           └───────────────┘
```

---

## Backend Module Responsibilities

| Module | Routes | Responsibility | Key Patterns |
|--------|--------|----------------|--------------|
| `auth` | `/auth/*` | Registration, login, JWT issuance/refresh, logout, account deletion | httpOnly cookies, bcrypt, role deps |
| `centres` | `/centres` | Centre CRUD, staff count, pagination | Subquery staff count, 30s cache |
| `surgeries` | `/surgeries` | Surgery CRUD, filtering (centre, dog, date) | FK cascades, indexes |
| `inspections` | `/inspections` | Inspection CRUD, scheduling, status transitions | FK cascades |
| `funds` | `/grants`, `/allocations`, `/expenses` | Grant lifecycle, allocation to centres, expense tracking with balance validation | Decimal money, allocation balance check |
| `public` | `/public/complaints`, `/sync/*` | Citizen complaints (public), offline sync queue with idempotency | Public create, auth list/update |
| `dogs` | `/dogs` | Dog registry (tag, sex, age, weight) | Centre FK cascade |

---

## Database Schema (Key Tables)

```
centres ──────┬── staff (centre_id FK, cascade)
              ├── dogs (centre_id FK, cascade)
              ├── surgeries (centre_id FK, cascade)
              ├── inspections (centre_id FK, cascade)
              ├── allocations (centre_id FK, cascade)
              └── complaints (centre_id FK, cascade)

grants ─────── allocations ────── expenses (allocation_id FK, cascade)
                                    └── surgery_id FK (nullable)
```

**Key Design Decisions:**
- **UUID PKs** (String(36)) — no sequence contention, portable
- **Naive UTC DateTime** — `datetime.now(UTC).replace(tzinfo=None)` for Postgres `TIMESTAMP WITHOUT TIME ZONE`
- **FK ON DELETE CASCADE** — deleting a centre cleans all dependent records
- **Indexes on all FKs** — query performance
- **Decimal(12,2) for money** — no floating-point drift
- **Soft delete not used** — cascade handles cleanup

---

## API Design

### Versioning
- All routes under `/api/v1/*`
- Legacy root-level routes preserved for backward compatibility (tests)

### Conventions
| Aspect | Standard |
|--------|----------|
| Resources | Plural, kebab-case (`/centres`, `/surgeries`) |
| Methods | GET=list, POST=create, GET/{id}=read, PATCH=update, DELETE=remove |
| Pagination | `?limit=50&offset=0` (default 50, max 100) |
| Filtering | `?centre_id=xxx&status=active` |
| Field Selection | *Planned* `?fields=id,name,code` |
| Errors | RFC 7807 Problem Details (planned) — currently `{"detail": "..."}` |

### Auth
- **Access Token:** 15 min, JWT HS256, in `Authorization: Bearer` + `httpOnly` cookie
- **Refresh Token:** 7 days, rotating, in `httpOnly` cookie
- **Roles:** `admin`, `vet`, `surgeon` — enforced via `require_role()` dependency

### Rate Limits
| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 5/min per IP |
| `POST /auth/register` | 3/hr per IP |
| General | 60/min per IP |

---

## Frontend Architecture

```
frontend/src/
├── components/          # Reusable UI (DataTable, StatCard, CentreFormModal, ChartPlaceholder)
├── contexts/
│   └── AuthContext.tsx  # Token management, user state, login/logout
├── pages/               # Route-level components
│   ├── Centres.tsx      # List + modal create, filters, pagination
│   ├── Surgeries.tsx    # List + summary stats, join centres
│   ├── Inspections.tsx  # List + status badges
│   ├── FundTracker.tsx  # 3 tabs (Grants, Allocations, Expenses)
│   ├── Dashboard.tsx    # Aggregated stats + charts
│   ├── Reports.tsx      # Static templates
│   └── CommitteePortal.tsx
├── services/api/        # Modular API client
│   ├── index.ts         # Barrel export + legacy `api` object
│   ├── auth.ts
│   ├── centres.ts
│   ├── surgeries.ts
│   ├── inspections.ts
│   ├── funds.ts
│   └── public.ts
├── types/index.ts       # Shared TS interfaces
└── layouts/DashboardLayout.tsx
```

**State Management:**
- React `useState`/`useEffect` for local UI state
- `AuthContext` for global auth (token, user, login/logout)
- No external state library (Zustand/Jotai) — not needed at this scale

**API Client:**
- Modular per-domain (`authApi`, `centresApi`, `surgeriesApi`, etc.)
- Single `request<T>()` wrapper with `credentials: 'include'`
- `setAuthToken()` syncs Bearer header across modules
- Legacy `api` object exported for gradual migration

---

## Caching Strategy

| Layer | Mechanism | TTL | Invalidation |
|-------|-----------|-----|--------------|
| **In-Memory** | `src/cache.py` (dict + TTL) | 30s (config) | `invalidate_pattern("centres:")` on write |
| **HTTP** | `Cache-Control: max-age=30` | 30s | N/A |
| **Redis** | *Future* | — | — |

**Current:** Centres list endpoint cached with pagination params in key. Invalidated on centre create.

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     REQUEST FLOW                             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ CorrelationIDMiddleware                                     │
│ - Generates/propagates X-Request-ID                         │
│ - Attaches to request.state.correlation_id                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Rate Limiter (slowapi)                                      │
│ - IP-based, configurable limits                             │
│ - 429 with Retry-After header                               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ CORS Middleware                                             │
│ - Whitelist origins only                                    │
│ - Credentials allowed                                       │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Security Headers Middleware                                 │
│ - HSTS, X-Content-Type-Options, X-Frame-Options, CSP       │
│ - CSP strict in prod, relaxed in dev                        │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Route Handlers (with require_role / get_current_user)       │
│ - JWT validation (HS256, exp, type)                         │
│ - Role enforcement                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development
```
Docker Compose
├── db (PostgreSQL 16)     → localhost:5432
├── redis (Redis 7)        → localhost:6379
├── backend (uvicorn)      → localhost:8000
└── frontend (vite dev)    → localhost:5173 (proxy /api → :8000)
```

### Production (Free Tier)
```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UptimeRobot (5-min ping)                      │
└─────────────────────────────────────────────────────────────────┘
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
┌───────────────────┐ ┌───────────────────┐
│  HF Spaces        │ │     Vercel        │
│  (Docker)         │ │   (Static)        │
│  Backend API      │ │  Frontend SPA     │
│  :8000            │ │  + /api proxy     │
└───────────────────┘ └───────────────────┘
          │                   │
          └─────────┬─────────┘
                    ▼
          ┌───────────────────┐
          │   Neon Postgres   │
          │  (Serverless)     │
          └───────────────────┘
                    │
                    ▼
          ┌───────────────────┐
          │   Upstash Redis   │
          │   (Free Tier)     │
          └───────────────────┘
```

**Keep-alive:** UptimeRobot pings `/health` every 5 min (HF Spaces suspends after 48h idle).

---

## Observability

| Signal | Implementation |
|--------|----------------|
| **Logs** | Structured `logging` with `correlation_id` in `global_exception_handler` |
| **Health** | `GET /health` → `{status, checks: {database, redis}}` |
| **Errors** | Generic 500 to client, full traceback in server logs with correlation ID |
| **Metrics** | *Planned* — Prometheus `/metrics` endpoint |

---

## Future Extensibility

| Area | Planned |
|------|---------|
| **API** | Field selection (`?fields=`), RFC 7807 errors, webhook notifications |
| **Auth** | MFA, SSO (OIDC), audit log for auth events |
| **Frontend** | Real charts (Recharts), Lucide icons, PWA offline support |
| **Sync** | Conflict resolution, delta sync, background worker |
| **Reports** | Excel/PDF generation (reportlab), scheduled email |
| **Infra** | Redis cache, Prometheus/Grafana, structured logging (structlog) |