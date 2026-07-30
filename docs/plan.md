# Phase 1 — Scaffold Plan

## Objective

Working FastAPI backend with PostgreSQL models, auth wireframe, CI pipeline, and Docker image. Six domain modules stubbed with health-check endpoints.

## Build Order

### Step 1: Project skeleton
- `pyproject.toml` with FastAPI, SQLAlchemy, Alembic, Pydantic v2, Celery, Redis
- `src/` package structure mirroring the 10-module boundary
- `Dockerfile` + `.dockerignore`
- `pytest` config with `asyncio_mode=auto`

### Step 2: Configuration & DB
- `src/config.py` — env-driven settings (DATABASE_URL, REDIS_URL, SECRET_KEY, etc.)
- `src/database.py` — async SQLAlchemy engine + session factory
- `src/models/` — all 10 domain models (Centre, Staff, Dog, Surgery, Inspection, Grant, Allocation, Expense, AuditEvent, Complaint)
- Alembic initial migration

### Step 3: Auth wireframe
- `src/auth/` — JWT creation/validation, password hashing, RBAC dependency
- `src/auth/models.py` — User + Role tables
- `src/auth/routes.py` — POST /auth/login, POST /auth/register (centre staff)

### Step 4: Domain stubs
- Each domain gets a router with `GET /health` and placeholder for CRUD
- `src/centres/`, `src/surgeries/`, `src/inspections/`, `src/funds/`, `src/committees/`, `src/public/`

### Step 5: CI + Docker
- `.github/workflows/ci.yml` — lint (ruff), typecheck (pyright), test (pytest), Docker build
- `Dockerfile` — multi-stage, slim image
- Verify `docker compose up` starts the app

### Step 6: First test
- DB connection test
- Model creation + query test
- Health endpoint test
- Auth token round-trip test

## P0 / P1 / P2

| Priority | Items |
|----------|-------|
| **P0** | Project skeleton, config, DB, models, auth, health endpoints, CI |
| **P1** | Domain CRUD endpoints, Alembic migrations, Docker Compose |
| **P2** | i18n setup, offline sync engine, audit event log |
