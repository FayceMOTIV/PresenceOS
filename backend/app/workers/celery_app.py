"""
PresenceOS - Celery Application Configuration

All crontab hours are in Europe/Paris timezone.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "presenceos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks",
        "app.workers.cm_tasks",
        "app.workers.content_tasks",
        "app.workers.brain_tasks",
        "app.workers.orchestrator_tasks",
        "app.workers.proactive_cm_tasks",
        "app.workers.breakout_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# ── Periodic tasks (beat schedule) ────────────────────────────────────
# All hours are Europe/Paris local time.
celery_app.conf.beat_schedule = {
    # ── Every minute / interval ──
    "check-scheduled-posts": {
        "task": "app.workers.tasks.check_scheduled_posts",
        "schedule": 60.0,
    },
    "autopilot-check-auto-publish": {
        "task": "app.workers.tasks.autopilot_check_auto_publish",
        "schedule": 900.0,  # Every 15 min
    },
    "poll-google-reviews": {
        "task": "app.workers.cm_tasks.poll_google_reviews_all",
        "schedule": 900.0,  # Every 15 min
    },
    "orchestrator-check-publish": {
        "task": "app.workers.orchestrator_tasks.autopilot_check_publish",
        "schedule": 600.0,  # Every 10 min
    },
    # ── Every hour ──
    "sync-all-metrics": {
        "task": "app.workers.tasks.sync_all_metrics",
        "schedule": crontab(minute=0),
    },
    # ── Night (3h Paris) ──
    "refresh-expiring-tokens": {
        "task": "app.workers.tasks.refresh_expiring_tokens",
        "schedule": crontab(hour=3, minute=0),
    },
    # ── Morning intelligence (6h-7h Paris) ──
    "generate-daily-ideas": {
        "task": "app.workers.tasks.generate_daily_ideas",
        "schedule": crontab(hour=6, minute=0),
    },
    "detect-trends-daily": {
        "task": "app.workers.orchestrator_tasks.detect_trends_daily",
        "schedule": crontab(hour=6, minute=30),
    },
    # ── Ilyas wake-up (7h Paris) ──
    "autopilot-daily-generate": {
        "task": "app.workers.tasks.autopilot_daily_generate",
        "schedule": crontab(hour=7, minute=0),
    },
    # ── Daily brief + orchestrator (8h Paris) ──
    "send-daily-brief-notif": {
        "task": "app.workers.content_tasks.send_daily_brief_notifications",
        "schedule": crontab(hour=8, minute=0),
    },
    "orchestrator-daily-generate": {
        "task": "app.workers.orchestrator_tasks.autopilot_daily_orchestrate",
        "schedule": crontab(hour=8, minute=0),
    },
    "orchestrator-gap-check": {
        "task": "app.workers.orchestrator_tasks.check_calendar_gaps",
        "schedule": crontab(hour=8, minute=30),
    },
    # ── Daily token refresh ──
    "refresh-meta-token": {
        "task": "app.workers.tasks.refresh_meta_token",
        "schedule": crontab(hour=4, minute=0),  # 4 AM UTC = 5 AM Paris
    },
    # ── Weekly Sunday ──
    "brain-weekly-reflection": {
        "task": "app.workers.brain_tasks.weekly_reflection_all_brands",
        "schedule": crontab(hour=6, minute=0, day_of_week=0),
    },
    "brain-weekly-visual-reflection": {
        "task": "app.workers.brain_tasks.weekly_visual_reflection_all",
        "schedule": crontab(hour=7, minute=0, day_of_week=0),
    },
    "orchestrator-weekly-planning": {
        "task": "app.workers.orchestrator_tasks.run_weekly_planning_all_brands",
        "schedule": crontab(hour=20, minute=0, day_of_week=0),
    },
    # ── Weekly Monday ──
    "proactive-weekly-cm": {
        "task": "app.workers.proactive_cm_tasks.proactive_weekly_all",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
    "gmb-weekly-post": {
        "task": "app.workers.tasks.gmb_weekly_post",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
}
