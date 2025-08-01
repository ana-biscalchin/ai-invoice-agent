# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOCKER_CONTAINER=1

# Build arguments for user configuration
ARG USER_ID=1000
ARG GROUP_ID=1000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Copy all project files (including README.md)
COPY . .

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --with dev --no-interaction --no-ansi

# Create non-root user with matching UID/GID
RUN groupadd -g ${GROUP_ID} appgroup \
    && useradd -u ${USER_ID} -g ${GROUP_ID} -d /home/appuser -m -s /bin/bash appuser

# Create necessary directories with correct permissions
RUN mkdir -p /app/extracted_texts /app/vector_store \
    && chown -R appuser:appgroup /app \
    && chmod -R 755 /app/extracted_texts /app/vector_store

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "app/main.py"] 