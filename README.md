# ABC Compliance Platform

Digital compliance infrastructure for Animal Birth Control (ABC) centres — a full-stack
dashboard for state animal welfare boards to register centres, track surgeries, run surprise
inspections, monitor fund disbursement, and generate compliance reports.

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI (Python 3.11) + SQLAlchemy 2 async + asyncpg |
| Frontend | React 18 + TypeScript + Vite |
| Database | PostgreSQL (Docker) |
| Cache | Redis |
| Auth | JWT (access + refresh, httpOnly cookies + bearer) |

## Modules

- **Centres** — registered ABC centre directory (capacity, status, compliance score)
- **Surgeries** — monthly surgery logs per centre
- **Inspections** — surprise inspection scheduling and execution
- **Fund Tracker** — program fund allocation, grants, and expense monitoring
- **Reports** — compliance reporting and export
- **Committee Portal** — governance oversight views

## Quick Start

### Backend

```bash
docker compose up -d db redis
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn src.main:app --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The dev server proxies API calls to `http://localhost:8000` (override with `VITE_API_URL`).

### Environment

Copy `.env.example` to `.env` and set `DATABASE_URL` to your Postgres. The Docker Compose
defaults create a database `abc_dashboard` owned by user `abc` on port `5432`.

## Tests

```bash
pytest
```

## License

AGPL v3 — see [LICENSE](LICENSE).
