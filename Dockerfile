# Use Python 3.11 slim-bookworm as the base image (newer pango libraries)
FROM python:3.11-slim-bookworm

# Set environment variable to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory in the container
WORKDIR /app

# Install required system dependencies for weasyprint HTML to PDF conversion
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfribidi0 \
    libgdk-pixbuf-2.0-0 \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    libglib2.0-dev \
    libjpeg62-turbo-dev \
    libopenjp2-7-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    pkg-config \
    libgirepository1.0-dev \
    libcairo-gobject2 \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-core \
    fonts-noto-cjk \
    netcat-openbsd \
    build-essential \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appuser && \
    adduser --system --ingroup appuser appuser

RUN python -m venv venv

# Install uv and use it for dependencies
COPY requirements.txt .
RUN pip install uv && \
    uv pip install --system -r requirements.txt && \
    uv pip install --system --upgrade langgraph           

# Copy the backend code, excluding the frontend folder
COPY --chown=appuser:appuser . .
RUN rm -rf frontend/

# Create temp_cvs directory for CV generation
RUN mkdir -p temp_cvs && chown -R appuser:appuser temp_cvs

# ============ DEBUG MODE - REMOVE IN PRODUCTION ============
# Create debug directory for HTML source storage (DEBUG ONLY)
RUN mkdir -p debug_html && chown -R appuser:appuser debug_html
# ============ END DEBUG MODE ============

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