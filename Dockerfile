# Sử dụng Python 3.11 làm base image
FROM python:3.11-slim

# Set environment variable to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Đặt thư mục làm việc trong container
WORKDIR /app

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    fonts-dejavu \
    fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appuser && \
    adduser --system --ingroup appuser appuser

# Create audio data directory and set permissions
RUN mkdir -p /data/audio && \
    chmod -R 777 /data/audio

RUN python -m venv venv

# Copy file yêu cầu và cài đặt dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY --chown=appuser:appuser . .

# Expose port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Create an entrypoint script within the Dockerfile
ENTRYPOINT ["/bin/bash", "-c", "\
if [ \"$SERVICE_TYPE\" = \"celery_worker\" ]; then \
    echo \"Starting Celery worker...\" && \
    python -m celery -A app.jobs.celery_worker worker --loglevel=debug --concurrency=${CELERY_WORKER_CONCURRENCY:-4}; \
else \
    echo \"Running database schema creation script...\" && \
    python /app/scripts/create_db_schema.py && \
    if [ \"$ENV\" = \"development\" ]; then \
        echo \"Starting API in local mode (with hot reload)\" && \
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug; \
    else \
        echo \"Starting API in production mode\" && \
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${WORKER_CONCURRENCY:-4} --log-level debug; \
    fi; \
fi"]