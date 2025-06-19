import os
from celery import Celery
from celery.schedules import crontab, timedelta
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')

app = Celery('movie_mate')

# Configure broker URL to use Redis
app.conf.broker_url = 'redis://redis:6379/0'

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
        "schedule": timedelta(days=5),  # Every 5 days
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
        "schedule": timedelta(days=5),  # Every 5 days
    },
}

# Optional: Configure result backend for Celery to use Redis as result backend
app.conf.result_backend = 'redis://redis:6379/1'

# Optional : Configure task time limits
app.conf.task_time_limit = 3600
app.conf.task_soft_time_limit = 3000

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request:{self.request!r}')
