import os

from celery import Celery


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


broker_url = _env("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = _env("CELERY_RESULT_BACKEND", broker_url)

celery_app = Celery(
    "docling_worker",
    broker=broker_url,
    backend=result_backend,
    include=["docling_worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=os.getenv("TZ", "UTC"),
    enable_utc=True,
)

