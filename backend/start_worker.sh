#!/bin/bash

# Production Worker Startup Script
echo "Starting Movie Mate Background Worker..."

# Set environment variables
export DJANGO_ENV=production
export DJANGO_SETTINGS_MODULE=config.settings.prod

# Wait for database to be ready
echo "Waiting for database connection..."
python manage.py wait_for_db --timeout=60

# Run migrations if needed
echo "Running database migrations..."
python manage.py migrate --noinput

# Start Celery worker
echo "Starting Celery worker with production settings..."
exec celery -A config worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    --prefetch-multiplier=1 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat
