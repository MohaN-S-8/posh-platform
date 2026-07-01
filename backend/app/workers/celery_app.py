from celery import Celery
import os

# Create the Celery app
celery_app = Celery(
    "posh_worker",
    broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Placeholder task — real tasks will be added per feature
@celery_app.task
def test_task(x, y):
    return x + y