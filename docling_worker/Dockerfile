FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
  && rm -rf /var/lib/apt/lists/*

COPY docling_worker/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY docling_worker /app/docling_worker

CMD ["celery", "-A", "docling_worker.celery_app", "worker", "--loglevel=INFO", "-Q", "docling"]

