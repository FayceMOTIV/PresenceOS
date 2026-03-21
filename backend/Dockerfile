# PresenceOS Backend - Dockerfile

FROM python:3.11-slim

LABEL maintainer="PresenceOS <dev@presenceos.local>"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libmagic1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (separate layer for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Create required directories
RUN mkdir -p /tmp/presenceos/uploads /tmp/presenceos_videos /data/music \
    && chown -R appuser:appuser /tmp/presenceos /tmp/presenceos_videos /data/music

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# SERVICE_ROLE controls which process starts:
#   web (default) → FastAPI + Uvicorn
#   worker        → Celery worker
#   beat          → Celery beat scheduler
ENV SERVICE_ROLE=web

CMD sh -c "\
  if [ \"$SERVICE_ROLE\" = 'worker' ]; then \
    celery -A app.workers.celery_app worker --loglevel=info --concurrency=2; \
  elif [ \"$SERVICE_ROLE\" = 'beat' ]; then \
    celery -A app.workers.celery_app beat --loglevel=info; \
  else \
    alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 140; \
  fi"
