# Use Python 3.11 slim-buster as the base image
FROM python:3.11-slim

# Set environment variable to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory in the container
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
    fonts-liberation \
    netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appuser && \
    adduser --system --ingroup appuser appuser

RUN python -m venv venv

# Install uv and use it for dependencies
COPY requirements.txt .
RUN pip install --system -r requirements.txt && \
    pip install --system --upgrade langgraph           

# Copy the backend code, excluding the frontend folder
COPY --chown=appuser:appuser . .
RUN rm -rf frontend/

# Expose port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Create an entrypoint script within the Dockerfile
ENTRYPOINT ["/bin/bash", "-c", "\
if [ \"$SERVICE_TYPE\" = \"celery_worker\" ]; then \
    python -m celery -A app.jobs.celery_worker worker --concurrency=${CELERY_WORKER_CONCURRENCY:-4}; \
else \
    if [ \"$ENV\" = \"development\" ]; then \
        echo \"Starting API in local mode (with hot reload)\" && \
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir ./app --log-level info; \
    else \
        echo \"Starting API in production mode\" && \
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${WORKER_CONCURRENCY:-4}; \
    fi; \
fi"]
