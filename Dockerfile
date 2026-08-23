FROM python:3.11-alpine AS builder

WORKDIR /app
COPY requirements.txt ./
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini ./
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt

FROM python:3.11-alpine

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src /app/src
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/alembic.ini /app/alembic.ini

# Create non-root user
RUN adduser -D -u 1000 appuser
USER appuser

ENV PORT=8080
EXPOSE 8080
# Run migrations; a real failure must kill the container (fail fast), while
# benign concurrent-migration races are filtered from the log only.
CMD ["sh", "-c", "if ! alembic upgrade head > /tmp/migrate.log 2>&1; then cat /tmp/migrate.log; exit 1; fi; grep -v -E '(already exists|overlaps)' /tmp/migrate.log || true; python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]