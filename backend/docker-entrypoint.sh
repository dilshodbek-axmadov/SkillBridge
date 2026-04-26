#!/bin/sh
# =============================================================================
# Entrypoint for the SkillBridge backend container.
#  - Applies pending Django migrations on every boot.
#  - Starts the command supplied as CMD (gunicorn by default).
# =============================================================================
set -e

echo "[entrypoint] Running database migrations..."
if [ "$RUN_MIGRATIONS" = "true" ]; then
    python manage.py migrate
fi
exec "$@"

# (Optional) collectstatic — uncomment if/when STATIC_ROOT is configured:
# python manage.py collectstatic --noinput

echo "[entrypoint] Starting: $*"
exec "$@"
