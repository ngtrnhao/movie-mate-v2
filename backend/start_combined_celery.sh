#!/bin/bash

# Combined Celery Worker + Beat Startup Script for Render
echo "Starting Combined Celery Service (Worker + Beat)..."
echo "This service includes:"
echo "  - Celery Worker - Process tasks"
echo "  - Celery Beat - Auto-schedule 27 tasks"
echo "  - Tasks: movie sync, cache updates, recommendations, etc."
echo ""

echo "Starting Celery Beat scheduler in background..."
celery -A config beat --loglevel=info --scheduler=celery.beat.PersistentScheduler --detach --pidfile=celerybeat.pid &

# Give beat a moment to start
sleep 3

echo "Beat scheduler started successfully"
echo ""

echo "Starting Celery Worker in foreground..."
echo "Worker will listen on queues: high_priority, batch_processing, default"
exec celery -A config worker --loglevel=info --concurrency=2 --max-tasks-per-child=100 --queues=high_priority,batch_processing,default
