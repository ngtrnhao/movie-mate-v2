import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')

app = Celery('movie_mate')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Configure celery beat schedule
app.conf.beat_schedule ={
    'sync_popular-movies':{
        'task': 'apps.movies.tasks.sync_popular_movies',
        'schedule': 3600.0,
        'args':(50,),
    },
    'update-movie-data':{
        'task': 'apps.movies.tasks.update_movie_data',
        'schedule': 86400.0,
        'args':(7,50),
    },
    'sync_top-rated-movies':{
        'task': 'apps.movies.tasks.sync_top_rated_movies',
        'schedule': 3600.0,
        'args':(50,),
    },
    'sync_upcoming-movies':{
        'task': 'apps.movies.tasks.sync_upcoming_movies',
        'schedule': 3600.0,
    }
}

# Optional: Configure result backend for Celery to use Redis as result backend
app.conf.result_backend = 'redis://redis:6379/1'

# Optional : Configure task time limits
app.conf.task_time_limit = 3600
app.conf.task_soft_time_limit = 3000

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request:{self.request!r}')
