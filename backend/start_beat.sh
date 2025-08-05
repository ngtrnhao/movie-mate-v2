#!/bin/bash

# Production Celery Beat Startup Script
echo "Starting Movie Mate Celery Beat Scheduler..."

# Set environment variables
export DJANGO_ENV=production
export DJANGO_SETTINGS_MODULE=config.settings.prod

# Wait for database to be ready
echo "Waiting for database connection..."
python manage.py wait_for_db --timeout=60

# Run migrations if needed
echo "Running database migrations..."
python manage.py migrate --noinput

# Start Celery Beat scheduler
echo "Starting Celery Beat scheduler..."
exec celery -A config beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --max-interval=300
