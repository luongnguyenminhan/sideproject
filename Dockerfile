# Sử dụng Python 3.11 làm base image
FROM python:3.11-slim

# Set environment variable to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Đặt thư mục làm việc trong container
WORKDIR /app

# Install required system dependencies including dos2unix
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    dos2unix \
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

# Copy the startup script and fix line endings and permissions
COPY startup.sh /app/
RUN dos2unix /app/startup.sh && \
    chmod +x /app/startup.sh && \
    chown appuser:appuser /app/startup.sh

# Copy toàn bộ mã nguồn vào container
COPY --chown=appuser:appuser . .

# Make absolutely sure the startup script is executable
RUN chmod 755 /app/startup.sh

# Expose port
EXPOSE 8000

# Switch to non-root user and set entrypoint
USER appuser
# ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/app/startup.sh"]