#!/bin/bash

# Check if the service type is specified
if [ "$SERVICE_TYPE" = "celery_worker" ]; then
    echo "Starting Celery worker..."
    cd /app && python -m celery -A app.jobs.celery_worker worker --loglevel=debug --concurrency=${CELERY_WORKER_CONCURRENCY:-4}
else
    # Run database schema creation script
    echo "Running database schema creation script..."
    python /app/scripts/create_db_schema.py

    # Get the number of workers from environment variable or default to 4
    API_WORKER_COUNT=${API_WORKERS:-4}
    
    # Start the application
    if [ "$ENV" = "development" ]; then
        echo "Starting API in local mode (with hot reload)"
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload  --log-level debug
    else
        echo "Starting API in production mode"
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${WORKER_CONCURRENCY:-4} --log-level debug
    fi
fi