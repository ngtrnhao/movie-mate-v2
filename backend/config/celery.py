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
        "schedule": timedelta(days=7),  # Every 5 days
    },
    "sync_top_rated_movies": {
        "task": "apps.movies.tasks.sync_top_rated_movies",
        "schedule": timedelta(days=7),  # Every 5 days
    },
    "sync_upcoming_movies": {
        "task": "apps.movies.tasks.sync_upcoming_movies",
        "schedule": timedelta(days=7),  # Every 5 days
    },
    "update_movie_cache": {
        "task": "apps.movies.tasks.update_movie_cache",
        "schedule": timedelta(days=7),
    },
    "refresh_genre_summary": {
        "task": "apps.metadata.tasks.refresh_genre_summary_unique_task",
        "schedule": timedelta(hours=6),  # Every 6 hours
    },
}

# Task time limits are now configured in Django settings
# CELERY_TASK_TIME_LIMIT and CELERY_TASK_SOFT_TIME_LIMIT

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request:{self.request!r}')
