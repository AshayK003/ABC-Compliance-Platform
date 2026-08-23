# ABC Compliance Platform

<div align="center">

[![CI](https://github.com/AshayK003/ABC-Compliance-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/AshayK003/ABC-Compliance-Platform/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.133-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791?logo=postgresql)](https://www.postgresql.org)
[![Tests](https://img.shields.io/badge/tests-105%20backend%20%C2%B7%2018%20frontend-brightgreen)]()
[![Status](https://img.shields.io/badge/status-active%20development-brightgreen)]()

</div>

**Digital compliance infrastructure for Animal Birth Control (ABC) centres** — a full-stack dashboard for state animal welfare boards to register centres, track surgeries, run surprise inspections, monitor fund disbursement, and generate compliance reports.

---

## ✨ Key Features

| Module | Description |
|--------|-------------|
| **Centres** | Registered ABC centre directory with capacity, status, and staff counts |
| **Surgeries** | Monthly surgery logs per centre with outcome tracking |
| **Inspections** | Surprise inspection scheduling, execution, and findings |
| **Fund Tracker** | Grants, allocations, and expense monitoring with balance enforcement |
| **Reports** | Filtered compliance reports with real PDF (themed) and Excel exports, state heatmap, YoY charts |
| **Committee Portal** | Governance oversight views for AWBI/state board officials |
| **Sync Queue** | Offline-first mutation queue with idempotency keys, usable by field staff |
| **User Management** | Admin approval of registrations, role/centre assignment, session revocation |
| **Dashboard** | Live compliance ratios, surgery trends, fund disbursement computed from real data |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React 19 + TS)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Centres  │ │Surgeries │ │Inspect.  │ │ Funds    │  ...       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       └────────────┼────────────┼────────────┘                   │
│                    ▼            ▼                                │
│         ┌─────────────────────────────┐                          │
│         │   services/api (modular)    │                          │
│         │  auth │ centres │ funds ... │                          │
│         └──────────────┬──────────────┘                          │
└────────────────────────┼─────────────────────────────────────────┘
                         │ HTTPS /api/v1/*  (Bearer + httpOnly cookies)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ /centres │ │/surgeries│ │/inspect. │ │ /funds   │  ...       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       └────────────┼────────────┼────────────┘                   │
│                    ▼            ▼                                │
│         ┌─────────────────────────────┐                          │
│         │ Correlation ID Middleware   │                          │
│         │ Rate Limiting (slowapi)     │                          │
│         │ JWT Auth + RBAC + scoping   │                          │
│         └──────────────┬──────────────┘                          │
└────────────────────────┼─────────────────────────────────────────┘
                         │ asyncpg
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL 16                               │
│   centres · surgeries · inspections · funds · sync · audit      │
└─────────────────────────────────────────────────────────────────┘
```

**Stack:**
- **Backend:** FastAPI 0.133 (Python 3.11), SQLAlchemy 2.0 async, asyncpg, Pydantic v2, slowapi, PyJWT, bcrypt
- **Frontend:** React 19, TypeScript, Vite, ECharts, code-splitting, self-hosted icon font (offline-safe)
- **Database:** PostgreSQL 16, Alembic migrations (4 revisions)
- **Auth:** JWT access (15 min) + refresh (7 days) in `httpOnly` cookies with `SameSite` tuned per environment; Bearer fallback; server-side token revocation
- **Deployment:** Docker Compose (single server), HF Spaces + Vercel + Neon (free-tier cloud)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Git

### 1. Clone & Configure
```bash
git clone https://github.com/AshayK003/ABC-Compliance-Platform.git
cd ABC-Compliance-Platform
cp .env.example .env   # set a strong SECRET_KEY (min 32 bytes)
```

### 2. Start Infrastructure
```bash
docker compose up -d db redis
# Postgres on localhost:5432, Redis on localhost:6379
```

### 3. Backend
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn src.main:app --port 8000 --reload
```
✅ API at `http://localhost:8000`  
✅ Swagger docs at `http://localhost:8000/docs` (dev only)  
✅ Health check at `http://localhost:8000/health`

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```
✅ UI at `http://localhost:5173`

### 5. Seed Demo Data (Optional)
```bash
# From project root, with backend running
DATABASE_URL="postgresql+asyncpg://abc:abc@localhost:5432/abc_dashboard" \
  python scripts/seed_awbi_centres.py
DATABASE_URL="postgresql+asyncpg://abc:abc@localhost:5432/abc_dashboard" \
  python scripts/seed_demo.py
```
Seeds the official AWBI centre list plus demo-scale operations data
(~10 grants, ~15 allocations, ~90 expenses, ~180 dogs with surgeries,
~80 inspections) **and an admin account:**

| Role | Phone | Password |
|------|-------|----------|
| Admin | `9999999999` | `demo123` |

Demo data is for evaluation environments only.

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | Postgres async connection string |
| `REDIS_URL` | ❌ | `redis://localhost:6379/0` | Reserved for future workers |
| `SECRET_KEY` | ✅ | — | JWT signing key (min 32 bytes; default value rejected) |
| `DEBUG` | ❌ | `false` | Dev CSP, Swagger docs, relaxed cookie flags (localhost only) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | ❌ | `7` | Refresh token TTL |
| `ALLOWED_ORIGINS` | ❌ | `["http://localhost:5173"]` | CORS origins (JSON list format) |
| `CACHE_ENABLED` | ❌ | `true` | In-memory response cache |
| `CACHE_TTL_SECONDS` | ❌ | `30` | Cache TTL |

---

## 🧪 Tests

```bash
# Backend — 91 unit/API tests + 14 real-database e2e tests
pytest -q -m "not e2e"          # mocked suite (no database needed)

# e2e suite: requires Docker Postgres with an abc_test database
docker exec <db-container> psql -U abc -d postgres \
  -c "CREATE DATABASE abc_test OWNER abc;"
DATABASE_URL=... E2E_DATABASE_URL='postgresql+asyncpg://abc:abc@localhost:5433/abc_test' pytest tests/test_e2e_regression.py -v

# Frontend
cd frontend
npm run typecheck               # tsc
npm test                        # vitest (18 tests)
npm run build                   # production build
```

The e2e regression suite exercises true HTTP flows against PostgreSQL:
cookie-only auth, FK validation on the public complaint endpoint,
cross-centre authorization (IDOR regressions), file-export bytes, and the
full registration → approval → login lifecycle.

---

## 📁 Project Structure

```
ABC-Compliance-Platform/
├── .github/workflows/ci.yml    # CI: lint → typecheck → test → build → audit
├── migrations/                 # Alembic migrations (4 revisions)
├── frontend/
│   ├── src/
│   │   ├── components/         # DataTable, modals, ComplianceHeatmap, charts
│   │   ├── contexts/           # AuthContext (token refresh), ThemeContext
│   │   ├── pages/              # Dashboard, Centres, Surgeries, Inspections,
│   │   │                       # FundTracker, Reports, CommitteePortal...
│   │   ├── services/api/       # Modular API client with 401 auto-refresh
│   │   └── types/index.ts      # Shared TS interfaces
│   └── public/fonts/           # Self-hosted Material Symbols (offline-safe)
├── scripts/
│   ├── seed_awbi_centres.py    # Official AWBI-recognised centre list
│   ├── seed_demo.py            # Idempotent demo-data seeder (+ admin account)
│   └── shrink_geojson.py       # Map-data size optimizer (one-off)
├── src/
│   ├── auth/                   # JWT, bcrypt, cookies, RBAC deps, user mgmt
│   ├── centres/                # Centre CRUD + staff count subquery
│   ├── surgeries/ inspections/ # Operational CRUD with centre scoping
│   ├── funds/                  # Grants → allocations → expenses (balance-checked)
│   ├── public/                 # Complaints, heatmap, compliance scores, sync queue
│   ├── reports/                # Filtered report generation + PDF/Excel exporters
│   ├── notifications/          # Per-user notification inbox
│   ├── models/base.py          # SQLAlchemy 2.0 models (FK cascades, indexes)
│   └── main.py                 # App factory, middleware, security headers
├── tests/                      # Mocked suite + real-DB e2e regressions
├── pyproject.toml
└── README.md
```

---

## 🔐 Security

See [SECURITY.md](SECURITY.md) for the full policy and reporting process.

- **Auth:** JWT in `httpOnly` cookies (`SameSite=Strict` locally, `None` cross-site in prod); short-lived access + revocable refresh tokens
- **Registration:** pending admin approval — no instant access
- **Authorization:** role-based checks plus object-level centre-scoping on entity writes (anti-IDOR)
- **Account deletion:** deactivation preserving referenced history, not hard-delete
- **Rate limiting:** 5/min login, 3/hr register, 10/hr public complaints
- **CSP:** strict in production; HSTS, nosniff, frame-deny everywhere
- **Input validation:** Pydantic v2 on every request body; FK existence checks return 400s, not 500s
- **SQL injection:** SQLAlchemy ORM only — no raw SQL
- **Secrets:** env-driven, validated at startup (32-byte minimum SECRET_KEY)
- **CI audits:** `pip-audit` + `npm audit --audit-level=high` on every push

---

## 📦 Deployment

### Production (Free Tier)

| Service | Platform | Notes |
|---------|----------|-------|
| Backend | Docker (HF Spaces or any container host) | `Dockerfile`, fail-fast migrations |
| Frontend | Vercel | `frontend/vercel.json` SPA rewrite |
| Database | Neon Postgres | pooled connection string, `ssl=require` |

**Keep-alive:** UptimeRobot 5-min ping on the backend `/health`.

### Docker Compose (Single Server)
```bash
docker compose up -d --build
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

**AGPL v3** — see [LICENSE](LICENSE).

> This license requires that if you modify and deploy this software as a network service, you must provide the corresponding source code to users. Suitable for public-sector / civic-tech deployments where transparency is mandated.

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/AshayK003/ABC-Compliance-Platform/issues)
- **Security:** [SECURITY.md](SECURITY.md) — private disclosure via GitHub Security Advisories

---

<div align="center">

**Built for AWBI & State Animal Welfare Boards** — open source, transparent, auditable.

</div>
