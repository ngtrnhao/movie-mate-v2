import os
from celery import Celery
from celery.schedules import crontab, timedelta
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')

app = Celery('movie_mate')

# Configure Celery to use Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Windows specific configurations
app.conf.worker_pool_restarts = True
app.conf.worker_max_tasks_per_child = 1
app.conf.beat_scheduler = 'celery.beat.PersistentScheduler'
app.conf.beat_schedule_filename = 'celerybeat-schedule'

# Configure celery beat schedule
app.conf.beat_schedule = {
    "sync_popular_movies": {
        "task": "apps.movies.tasks.sync_popular_movies",
        "schedule": timedelta(minutes=10),  # Every 1 minutes
    },
    "sync_top_rated_movies": {
        "task": "apps.movies.tasks.sync_top_rated_movies",
        "schedule": timedelta(days=5),  # Every 5 days
    },
    "sync_upcoming_movies": {
        "task": "apps.movies.tasks.sync_upcoming_movies",
        "schedule": timedelta(days=5),  # Every 5 days
    },
    "update_movie_cache": {
        "task": "apps.movies.tasks.update_movie_cache",
        "schedule": timedelta(minutes=10),
    },
    "refresh_genre_summary": {
        "task": "apps.metadata.tasks.refresh_genre_summary_task",
        "schedule": timedelta(hours=6),  # Every 6 hours
    },

    # 🔄 Auto-processing tasks
    "process_user_interactions_frequent": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": timedelta(minutes=15),  # Every 15 minutes
        "kwargs": {"hours": 1}  # Process last 1 hour (changed from 0.25)
    },
    "process_user_interactions_hourly": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": timedelta(hours=0.25),  # Every hour
        "kwargs": {"hours": 1}  # Last 1 hour
    },
    "sync_trending_categories": {
        "task": "apps.movies.tasks.sync_trending_categories_auto",
        "schedule": timedelta(hours=6),  # Every 6 hours
    },

    # 📅 Scheduling automation tasks
    "process_scheduled_actions": {
        "task": "apps.movies.tasks.process_scheduled_actions_auto",
        "schedule": timedelta(minutes=5),  # Every 5 minutes
        "options": {"priority": 9}  # High priority for timely execution
    },
    "update_scheduling_status": {
        "task": "apps.movies.tasks.update_scheduling_status_auto",
        "schedule": timedelta(hours=1),  # Every hour
        "options": {"priority": 5}  # Normal priority
    },

    # 📊 Quality automation tasks
    "calculate_quality_new_movies": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(hours=2),  # Every 2 hours
        "kwargs": {"target_type": "new", "batch_size": 25, "max_movies": 100},
        "options": {"priority": 6}  # Medium priority
    },
    "calculate_quality_low_quality": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(hours=12),  # Twice daily
        "kwargs": {"target_type": "low_quality", "batch_size": 20, "max_movies": 50},
        "options": {"priority": 4}  # Lower priority
    },
    "calculate_quality_outdated": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(days=1),  # Daily
        "kwargs": {"target_type": "outdated", "batch_size": 30, "max_movies": 200},
        "options": {"priority": 3}  # Low priority
    },
    "quality_maintenance": {
        "task": "apps.movies.tasks.quality_maintenance_auto",
        "schedule": timedelta(days=1),  # Daily
        "options": {"priority": 2}  # Very low priority
    },
}

# Task time limits are now configured in Django settings
# CELERY_TASK_TIME_LIMIT and CELERY_TASK_SOFT_TIME_LIMIT

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request:{self.request!r}')
