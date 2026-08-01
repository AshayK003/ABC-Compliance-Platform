FROM python:3.11-alpine AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir --only-binary :all: .

COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .
RUN pip install --no-cache-dir --only-binary :all: .

FROM python:3.11-alpine

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src /app/src
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/alembic.ini /app/alembic.ini

ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "alembic upgrade head 2>&1 | grep -v -E '(already exists|overlaps)' || true; python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]