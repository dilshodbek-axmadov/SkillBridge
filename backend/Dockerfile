# syntax=docker/dockerfile:1.6
# =============================================================================
# SkillBridge backend — production Dockerfile (Azure-ready)
# =============================================================================
# Image runs the Django app under gunicorn on port 8000.
# Designed for:
#   - Azure App Service for Containers   (set WEBSITES_PORT=8000)
#   - Azure Container Apps               (target port = 8000)
# Celery workers / beat can reuse the SAME image — just override the CMD:
#   docker run ... <image> celery -A skillbridge worker -l info
# =============================================================================

ARG PYTHON_VERSION=3.11

# -----------------------------------------------------------------------------
# Stage 1: builder — compile wheels in a fat image so the final stage stays slim
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Build-only system deps (gcc, headers for psycopg2, Pillow, lxml, Levenshtein)
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        gcc \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Pre-build wheels into /wheels so the runtime stage can pip-install without gcc.
RUN pip wheel --wheel-dir /wheels -r requirements.txt gunicorn==21.2.0


# -----------------------------------------------------------------------------
# Stage 2: runtime — slim image with only the runtime libraries
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=skillbridge.settings \
    PORT=8000

# Runtime-only system deps:
#   libpq5     -> psycopg2-binary
#   libmagic1  -> python-magic (file-type sniffing)
#   libjpeg62  -> Pillow
#   curl       -> healthcheck
RUN apt-get update && apt-get install --no-install-recommends -y \
        libpq5 \
        libmagic1 \
        libjpeg62-turbo \
        zlib1g \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

# Install pre-built wheels from the builder stage
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels \
        -r requirements.txt gunicorn==21.2.0 \
    && rm -rf /wheels

# spaCy English model (used by apps/users/cv_parser/nlp_extractor.py)
RUN python -m spacy download en_core_web_sm

# NLTK corpora used by transformers / nltk-based fallbacks (small footprint)
RUN python -m nltk.downloader -d /usr/share/nltk_data punkt stopwords || true

# Copy application source
COPY . .

# Writable dirs for media uploads, static files, and HF / sentence-transformers cache
RUN mkdir -p /app/media /app/staticfiles /app/.cache \
    && chown -R app:app /app

# Cache directory for sentence-transformers / HuggingFace so the model is
# downloaded once at first request and persisted on the container's volume.
ENV HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

USER app

EXPOSE 8000

# Healthcheck — Azure ignores HEALTHCHECK but local docker run benefits from it.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:${PORT}/admin/login/ || exit 1

# Entry point script: applies migrations, then starts gunicorn.
COPY --chown=app:app docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "skillbridge.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "2", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
