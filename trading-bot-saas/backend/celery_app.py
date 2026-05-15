"""
Celery Application Configuration
Handles background tasks for multi-tenant trading bot execution
"""

from celery import Celery
from celery.schedules import crontab
import os

# Redis configuration (backend + broker)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    'trading_bot_saas',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks']  # Import tasks module
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Performance settings
    worker_prefetch_multiplier=1,  # One task per worker at a time
    task_acks_late=True,  # Acknowledge task after completion
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks

    # Task execution
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=360,  # 6 minutes hard limit

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },

    # Retry settings
    task_default_retry_delay=60,  # Retry after 60 seconds
    task_max_retries=3,

    # Concurrency
    worker_concurrency=4,  # Number of concurrent workers

    # Beat schedule (periodic tasks)
    beat_schedule={
        'check-active-bots-every-minute': {
            'task': 'tasks.check_and_run_bots',
            'schedule': 60.0,  # Run every 60 seconds
        },
        'update-bot-metrics-every-5-minutes': {
            'task': 'tasks.update_all_bot_metrics',
            'schedule': 300.0,  # Run every 5 minutes
        },
        'cleanup-old-data-daily': {
            'task': 'tasks.cleanup_old_data',
            'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
        }
    }
)

if __name__ == '__main__':
    celery_app.start()
