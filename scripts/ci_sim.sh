#!/bin/bash
# CI simulation runner — mirrors .github/workflows/ci.yml backend job against a real Postgres
set -e

cd "$(dirname "$0")/.."
DB_URL="${DB_URL:-postgresql+asyncpg://abc:abc@db:5432/abc_test_ci}"
SECRET="${SECRET:-ci-test-secret-key-not-for-production}"

docker run --rm --network abc-compliance-platform_default \
  -v "$(pwd)/src:/app/src" \
  -v "$(pwd)/tests:/app/tests" \
  -v "$(pwd)/migrations:/app/migrations" \
  -v "$(pwd)/pyproject.toml:/app/pyproject.toml" \
  -v "$(pwd)/alembic.ini:/app/alembic.ini" \
  -e DATABASE_URL="$DB_URL" \
  -e SECRET_KEY="$SECRET" \
  -e RUN_INTEGRATION="${RUN_INTEGRATION:-1}" \
  -e PYTHONPATH="/app" \
  abc-backend:test sh -c "
    pip install -q --only-binary :all: --ignore-scripts pytest pytest-asyncio httpx 2>&1 | tail -1
    cd /app
    echo '=== ALEMBIC UPGRADE ==='
    python -m alembic upgrade head 2>&1 | tail -3
    echo '=== ALEMBIC CHECK ==='
    python -m alembic check 2>&1 | tail -2
    echo '=== TESTS ==='
    python -m pytest \"\$@\" -v 2>&1 | tail -30
  " sh "$@"
