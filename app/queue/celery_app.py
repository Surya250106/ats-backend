from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ats_worker",
    broker=settings.QUEUE_URL,
    backend=settings.QUEUE_URL,
    include=["app.workers.tasks"]
)

# Apply configurations for serializing messages and managing task results
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
