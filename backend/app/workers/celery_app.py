"""
PresenceOS - Celery Application Configuration
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "presenceos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Periodic tasks (beat schedule)
celery_app.conf.beat_schedule = {
    # Check for scheduled posts every minute
    "check-scheduled-posts": {
        "task": "app.workers.tasks.check_scheduled_posts",
        "schedule": 60.0,  # Every minute
    },
    # Sync metrics every hour
    "sync-all-metrics": {
        "task": "app.workers.tasks.sync_all_metrics",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Generate daily ideas at 6 AM
    "generate-daily-ideas": {
        "task": "app.workers.tasks.generate_daily_ideas",
        "schedule": crontab(hour=6, minute=0),
    },
    # Refresh expiring tokens daily
    "refresh-expiring-tokens": {
        "task": "app.workers.tasks.refresh_expiring_tokens",
        "schedule": crontab(hour=3, minute=0),
    },
    # Autopilot: generate daily content at 7 AM UTC
    "autopilot-daily-generate": {
        "task": "app.workers.tasks.autopilot_daily_generate",
        "schedule": crontab(hour=7, minute=0),
    },
    # Autopilot: check for auto-publish every 15 minutes
    "autopilot-check-auto-publish": {
        "task": "app.workers.tasks.autopilot_check_auto_publish",
        "schedule": 900.0,  # Every 15 minutes
    },
}
