#!/bin/sh
set -e

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput

echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Migrating django_celery_results..."
python manage.py migrate django_celery_results --noinput

echo "[entrypoint] Migrating django_celery_beat..."
python manage.py migrate django_celery_beat --noinput

echo "[entrypoint] Starting Celery worker in background..."
celery -A skillbridge worker --loglevel=info &

echo "[entrypoint] Starting Celery beat in background..."
celery -A skillbridge beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

echo "[entrypoint] Ensuring superuser exists..."
python manage.py ensure_superuser

echo "[entrypoint] Starting: $*"
exec "$@"