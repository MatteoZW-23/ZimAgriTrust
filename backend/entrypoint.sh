#!/bin/bash
# Production entrypoint — runs Alembic migrations before starting the server.
# This ensures schema is always up-to-date before any requests are served.
# Designed to be idempotent: safe to run on every container restart.
set -euo pipefail

echo "[entrypoint] Starting ZimAgriTrust backend..."
echo "[entrypoint] Environment: ${APP_ENV:-unknown}"

# ── Validation: refuse to start with placeholder secrets ──────────────────
if echo "${SECRET_KEY:-}" | grep -qE "CHANGE_ME|test-key|your-secret|secret-bootstrap"; then
    echo "[entrypoint] FATAL: SECRET_KEY is a placeholder. Set a real secret before deploying."
    exit 1
fi

if [ "${MASTER_TEST_LOGIN_ENABLED:-false}" = "true" ] && [ "${APP_ENV:-}" = "production" ]; then
    echo "[entrypoint] FATAL: MASTER_TEST_LOGIN_ENABLED=true in production environment. Refusing to start."
    exit 1
fi

# ── Wait for PostgreSQL to be ready ───────────────────────────────────────
echo "[entrypoint] Waiting for PostgreSQL..."
MAX_RETRIES=30
RETRY_COUNT=0
until python -c "
import psycopg2, os, sys
try:
    # Convert SQLAlchemy URL to psycopg2 format
    db_url = os.environ['DATABASE_URL'].replace('postgresql+psycopg2://', 'postgresql://')
    psycopg2.connect(db_url)
    sys.exit(0)
except Exception as e:
    print(f'  DB not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "[entrypoint] FATAL: PostgreSQL not available after $MAX_RETRIES attempts. Exiting."
        exit 1
    fi
    echo "[entrypoint]   Retrying in 2s... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done
echo "[entrypoint] PostgreSQL is ready."

# ── Run Alembic migrations ────────────────────────────────────────────────
echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head
echo "[entrypoint] Migrations complete."

# ── Start the application ─────────────────────────────────────────────────
echo "[entrypoint] Starting Gunicorn..."
exec gunicorn app.main:app \
    --workers "${GUNICORN_WORKERS:-4}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:8000" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --graceful-timeout 30 \
    --max-requests "${GUNICORN_MAX_REQUESTS:-1000}" \
    --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-100}" \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level "${GUNICORN_LOG_LEVEL:-info}"
