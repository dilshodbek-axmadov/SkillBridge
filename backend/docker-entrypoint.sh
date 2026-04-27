#!/bin/sh
set -e

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput

echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Ensuring superuser exists..."
python manage.py ensure_superuser

echo "[entrypoint] Starting: $*"
exec "$@"