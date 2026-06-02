"""
Celery Application for ZimAgriTrust Background Tasks - Production Hardened
"""
import os
from celery import Celery

# Get Redis URL from environment
redis_url = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Create Celery app
celery_app = Celery(
    "zimagritrust",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.worker.tasks",
    ]
)

# Celery configuration - Production Hardened
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Harare",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Retry configuration with exponential backoff
    task_default_retry_delay=60,  # 1 minute initial delay
    task_max_retries=3,
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # 10 minutes max backoff
    task_retry_jitter=True,
    
    # Dead-letter queue for failed tasks
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "high_priority": {
            "exchange": "high_priority",
            "routing_key": "high_priority",
        },
        "low_priority": {
            "exchange": "low_priority",
            "routing_key": "low_priority",
        },
        "dead_letter": {
            "exchange": "dead_letter",
            "routing_key": "dead_letter",
        },
    },
    task_default_exchange="default",
    task_default_routing_key="default",
    task_default_exchange_type="direct",
    
    # Task result expiration
    result_expires=3600,  # 1 hour
    
    # Worker optimization
    worker_disable_rate_limits=True,
    worker_send_task_events=True,
    
    # Acknowledgment and reliability
    task_acks_late=True,  # Ack after task completes (not before)
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    
    # Event stream for monitoring
    worker_send_sent_event=True,
)

# Configure result backend expiration
celery_app.conf.result_expires = 3600  # 1 hour
