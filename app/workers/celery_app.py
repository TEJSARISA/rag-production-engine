from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "rag_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_routes={"process_document_task": {"queue": "documents"}},
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)
