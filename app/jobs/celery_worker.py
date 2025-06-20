from celery import Celery

from app.core.config import Settings

# Khởi tạo Celery
settings = Settings()
print(settings.CELERY_BROKER_URL)
print("Celery worker is starting...")
celery_app = Celery(
    "enterviu-ai-worker",  # More descriptive app name
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.jobs.tasks"],  # Include tasks module
)

# No need to autodiscover_tasks if we explicitly include the tasks module
# celery_app.autodiscover_tasks(["app.jobs.tasks"])

celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    worker_max_memory_per_child=500000 * 2 * 32,  # 500MB
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks
    # Task execution settings
    task_acks_late=True,  # Only acknowledge after the task is completed
    task_reject_on_worker_lost=True,  # Requeue task if worker is killed
    # Task time limits to prevent hanging tasks
    task_time_limit=24 * 60 * 60,  # 24 hours (comment corrected)
    task_soft_time_limit=24 * 60 * 60,  # 24 hours (comment corrected)
)

if __name__ == "__main__":
    celery_app.start()
