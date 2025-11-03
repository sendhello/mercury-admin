#!/usr/bin/env sh
set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Run database migrations
python manage.py migrate

# Start application server (Gunicorn + Uvicorn worker)
exec gunicorn main:app \
  --workers "${WORKERS}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "${HOST}:${PORT}" \
  --log-level "${LOG_LEVEL}"
