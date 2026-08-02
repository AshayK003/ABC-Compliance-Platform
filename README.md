# ABC Compliance Platform

<div align="center">

[![CI](https://github.com/AshayK003/ABC-Compliance-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/AshayK003/ABC-Compliance-Platform/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5%2B-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791?logo=postgresql)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7%2B-DC382D?logo=redis)](https://redis.io)
[![Tests](https://img.shields.io/badge/tests-61%20passed%2C%204%20skipped-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-82%25-yellow)]()
[![Status](https://img.shields.io/badge/status-active%20development-brightgreen)]()

</div>

**Digital compliance infrastructure for Animal Birth Control (ABC) centres** — a full-stack dashboard for state animal welfare boards to register centres, track surgeries, run surprise inspections, monitor fund disbursement, and generate compliance reports.

---

## ✨ Key Features

| Module | Description |
|--------|-------------|
| **Centres** | Registered ABC centre directory with capacity, status, compliance score, and staff count |
| **Surgeries** | Monthly surgery logs per centre with outcome tracking (recovered, complications) |
| **Inspections** | Surprise inspection scheduling, execution, and findings with sign-off |
| **Fund Tracker** | Program fund allocation, grants, and expense monitoring with budget vs actuals |
| **Reports** | Compliance reporting and export (templates ready for Excel/PDF), including a state-level compliance heatmap |
| **Committee Portal** | Governance oversight views for AWBI/state board officials |
| **Sync Queue** | Offline-first mutation queue with idempotency keys for unreliable connectivity |
| **Dashboard** | Real-time compliance trends, surgery/fund/centre metrics computed from live data |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React 18 + TS)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Centres  │ │Surgeries │ │Inspect.  │ │ Funds    │  ...       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       └────────────┼────────────┼────────────┘                   │
│                    ▼            ▼                                 │
│         ┌─────────────────────────────┐                           │
│         │   api.ts (modular clients)  │                           │
│         │  auth │ centres │ funds ... │                           │
│         └──────────────┬──────────────┘                           │
└───────────────────────┼──────────────────────────────────────────┘
                        │ HTTPS /api/v1/*
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ /centres │ │/surgeries│ │/inspect. │ │ /funds   │  ...       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       └────────────┼────────────┼────────────┘                   │
│                    ▼            ▼                                 │
│         ┌─────────────────────────────┐                           │
│         │   Correlation ID Middleware │                           │
│         │   Rate Limiter (slowapi)    │                           │
│         │   JWT Auth (httpOnly cookies)│                          │
│         └──────────────┬──────────────┘                           │
└───────────────────────┼──────────────────────────────────────────┘
                        │ asyncpg
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL (Docker)                         │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌─────────┐            │
│  │centres  │ │surgeries │ │inspections│ │ funds*  │  ...       │
│  └─────────┘ └──────────┘ └───────────┘ └─────────┘            │
└─────────────────────────────────────────────────────────────────┘
                        ▲
                        │ Redis (cache, rate limit, sync queue)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        REDIS (Docker)                            │
└─────────────────────────────────────────────────────────────────┘
```

**Stack:**
- **Backend:** FastAPI 0.115+ (Python 3.11), SQLAlchemy 2.0 async, asyncpg, Pydantic v2, slowapi (rate limiting), JWT (HS256)
- **Frontend:** React 18, TypeScript 5, Vite 5, React.lazy code-splitting, TanStack Table patterns (custom DataTable), CSS Modules
- **Database:** PostgreSQL 16 (Docker), SQLAlchemy 2.0 ORM with async session
- **Cache:** Redis 7 (Docker) — in-memory fallback when unavailable
- **Auth:** JWT access (15 min) + refresh (7 days) tokens in `httpOnly` `SameSite=Strict` cookies with auto-refresh on 401
- **Deployment:** Docker Compose (local), HF Spaces + Vercel (prod)

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
cp .env.example .env   # edit DATABASE_URL if needed
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
✅ UI at `http://localhost:5173` (proxies `/api` → `localhost:8000`)

### 5. Seed Demo Data (Optional)
```bash
# From project root, with backend running
DATABASE_URL="postgresql+asyncpg://abc:abc@localhost:5432/abc_dashboard" \
  python scripts/seed_demo.py
```
Populates 3 centres, 4 surgeries, 2 inspections, 2 grants, 3 allocations, 4 expenses.

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | Postgres async connection string |
| `REDIS_URL` | ❌ | `redis://localhost:6379/0` | Redis connection string |
| `SECRET_KEY` | ✅ | — | JWT signing key (min 32 chars) |
| `DEBUG` | ❌ | `false` | Enable dev CSP, Swagger docs |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | ❌ | `7` | Refresh token TTL |
| `ALLOWED_ORIGINS` | ❌ | `["http://localhost:5173"]` | CORS origins |
| `CACHE_ENABLED` | ❌ | `true` | Enable in-memory cache |
| `CACHE_TTL_SECONDS` | ❌ | `30` | Cache TTL |

---

## 🧪 Tests

```bash
# Backend
pytest -q                    # 71 passed, 4 skipped
pytest --cov=src --cov-report=term-missing

# Frontend
cd frontend
npm run lint                 # ESLint + TypeScript
npm run typecheck            # tsc --noEmit
npm run build                # Production build
```

---

## 📁 Project Structure

```
ABC-Compliance-Platform/
├── .github/workflows/ci.yml     # CI: lint → typecheck → test → build → audit
├── alembic/                     # DB migrations (2 versions)
├── frontend/
│   ├── src/
│   │   ├── components/          # DataTable, StatCard, CentreFormModal, ChartPlaceholder
│   │   ├── contexts/AuthContext.tsx
│   │   ├── pages/               # Centres, Surgeries, Inspections, FundTracker, Dashboard, Reports
│   │   ├── services/api/        # Modular API client (auth, centres, surgeries, inspections, funds, public)
│   │   └── types/index.ts       # Shared TS interfaces
│   └── package.json
├── scripts/
│   └── seed_demo.py             # Idempotent demo data seeder
├── src/
│   ├── auth/                    # JWT, bcrypt, httpOnly cookies, role-based deps
│   ├── centres/                 # Centre CRUD + staff count subquery
│   ├── surgeries/               # Surgery CRUD with filtering
│   ├── inspections/             # Inspection CRUD + scheduling
│   ├── funds/                   # Grants, Allocations, Expenses + balance validation
│   ├── public/                  # Complaints (public), Sync Queue (offline)
│   ├── models/base.py           # SQLAlchemy 2.0 models (FK cascades, indexes, relationships)
│   ├── cache.py                 # In-memory TTL cache (30s) with invalidation
│   ├── config.py                # Pydantic Settings (env-driven)
│   ├── database.py              # Async engine + session
│   └── main.py                  # FastAPI app, middleware, lifespan, v1 router
├── tests/                       # 71 async tests (auth, centres, funds, health, sync)
├── pyproject.toml
└── README.md
```

---

## 🔐 Security

- **Secrets:** All in environment variables, validated on startup
- **Auth:** JWT in `httpOnly` `Secure` `SameSite=Strict` cookies; short-lived access + rotating refresh
- **Authorization:** Role-based (`admin`, `vet`, `surgeon`) via `require_role()` dependency
- **Rate Limiting:** 5/min login, 3/hr register, 60/min general (slowapi)
- **CSP:** Strict in production (`script-src 'self'`), relaxed in dev
- **Input Validation:** Pydantic v2 on every request body
- **SQL Injection:** SQLAlchemy ORM only — no raw SQL
- **CORS:** Whitelist only (`http://localhost:5173` dev, configured origins prod)
- **Error Handling:** Generic 500 messages, structured logging with correlation IDs

---

## 📦 Deployment

### Production (Free Tier)

| Service | Platform | Config |
|---------|----------|--------|
| Backend | Hugging Face Spaces (Docker) | `Dockerfile`, `scripts/deploy_hf.py` |
| Frontend | Vercel | `vercel.json` + `VITE_API_URL` |
| Database | Neon Postgres | Serverless, auto-suspend |
| Cache | Redis (if needed) | Upstash free tier |

**Keep-alive:** UptimeRobot 5-min ping (HF Spaces suspends after 48h idle)

### Docker Compose (Single Server)
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup (pre-commit, virtual env, test runner)
- Code style (black, isort, flake8, mypy, ESLint + Prettier)
- PR workflow (branch naming, conventional commits, review checklist)
- Testing requirements (auth, validation, error paths)

---

## 📄 License

**AGPL v3** — see [LICENSE](LICENSE).

> This license requires that if you modify and deploy this software as a network service, you must provide the corresponding source code to users. Suitable for public-sector / civic-tech deployments where transparency is mandated.

---

## 🙏 Acknowledgements

- **FastAPI** — modern, fast web framework
- **SQLAlchemy 2.0** — async ORM with 20 years of battle-testing
- **React + TypeScript + Vite** — frontend DX gold standard
- **PostgreSQL** — the world's most advanced open-source database
- **Redis** — in-memory data structure store
- **slowapi** — FastAPI rate limiting
- **Pydantic v2** — data validation using Python type hints

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/AshayK003/ABC-Compliance-Platform/issues)
- **Discussions:** [GitHub Discussions](https://github.com/AshayK003/ABC-Compliance-Platform/discussions)
- **Security:** See [SECURITY.md](SECURITY.md) for responsible disclosure

---

<div align="center">

**Built for AWBI & State Animal Welfare Boards** — open source, transparent, auditable.

</div>