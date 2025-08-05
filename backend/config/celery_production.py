import os
from celery import Celery
from celery.schedules import crontab, timedelta
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

app = Celery('movie_mate_production')

# Configure Celery to use Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Production specific configurations
app.conf.update(
    # Worker settings
    worker_pool_restarts=True,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    worker_concurrency=2,

    # Task settings
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Beat settings
    beat_scheduler='celery.beat.PersistentScheduler',
    beat_schedule_filename='celerybeat-schedule',
    beat_max_loop_interval=300,  # 5 minutes

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': "mymaster",
        'visibility_timeout': 3600,
    },

    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Serialization
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',

    # Timezone
    timezone='UTC',
    enable_utc=True,
)

# Configure celery beat schedule for production
app.conf.beat_schedule = {
    # Movie sync tasks (less frequent in production)
    "sync_popular_movies": {
        "task": "apps.movies.tasks.sync_popular_movies",
        "schedule": timedelta(days=7),  # Weekly instead of daily
    },
    "sync_top_rated_movies": {
        "task": "apps.movies.tasks.sync_top_rated_movies",
        "schedule": timedelta(days=7),
    },
    "sync_upcoming_movies": {
        "task": "apps.movies.tasks.sync_upcoming_movies",
        "schedule": timedelta(days=3),  # Every 3 days
    },

    # Cache update tasks
    "update_movie_cache": {
        "task": "apps.movies.tasks.update_movie_cache",
        "schedule": timedelta(minutes=30),  # Every 30 minutes
    },
    "refresh_genre_summary": {
        "task": "apps.metadata.tasks.refresh_genre_summary_task",
        "schedule": timedelta(hours=12),  # Twice daily
    },

    # User interaction processing (less frequent)
    "process_user_interactions_frequent": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": timedelta(hours=1),  # Hourly instead of every 15 minutes
        "kwargs": {"hours": 2}
    },
    "process_user_interactions_hourly": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": timedelta(hours=1),
        "kwargs": {"hours": 1}
    },

    # Trending categories
    "sync_trending_categories": {
        "task": "apps.movies.tasks.sync_trending_categories_auto",
        "schedule": timedelta(hours=6),  # Every 6 hours
    },

    # Scheduling automation
    "process_scheduled_actions": {
        "task": "apps.movies.tasks.process_scheduled_actions_auto",
        "schedule": timedelta(minutes=15),  # Every 15 minutes
        "options": {"priority": 9}
    },
    "update_scheduling_status": {
        "task": "apps.movies.tasks.update_scheduling_status_auto",
        "schedule": timedelta(hours=2),  # Every 2 hours
        "options": {"priority": 5}
    },

    # Quality metrics (less frequent in production)
    "calculate_quality_new_movies": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(hours=6),  # Every 6 hours
        "kwargs": {"target_type": "new", "batch_size": 20, "max_movies": 50},
        "options": {"priority": 6}
    },
    "calculate_quality_low_quality": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(days=1),  # Daily
        "kwargs": {"target_type": "low_quality", "batch_size": 15, "max_movies": 30},
        "options": {"priority": 4}
    },
    "calculate_quality_outdated": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(days=2),  # Every 2 days
        "kwargs": {"target_type": "outdated", "batch_size": 25, "max_movies": 100},
        "options": {"priority": 3}
    },
    "quality_maintenance": {
        "task": "apps.movies.tasks.quality_maintenance_auto",
        "schedule": timedelta(days=1),
        "options": {"priority": 2}
    },

    # Recommendation system tasks
    "update_user_similarities": {
        "task": "apps.users.tasks.update_user_similarities_batch",
        "schedule": timedelta(hours=12),  # Twice daily
        "options": {"priority": 7}
    },
    "generate_recommendations_active_users": {
        "task": "apps.users.tasks.generate_recommendations_for_active_users",
        "schedule": timedelta(hours=4),  # Every 4 hours
        "options": {"priority": 8}
    },

    # Cleanup tasks
    "cleanup_expired_recommendations": {
        "task": "apps.recommendations.tasks.cleanup_expired_recommendations",
        "schedule": timedelta(hours=24),  # Daily
        "options": {"priority": 3}
    },

    # Auto-management for large user bases
    "auto_manage_large_user_base": {
        "task": "apps.recommendations.tasks.auto_manage_large_user_base",
        "schedule": timedelta(hours=12),  # Twice daily
        "options": {"priority": 8}
    },

    # Bulk recommendation refresh
    "bulk_refresh_stale_recommendations_weekly": {
        "task": "apps.recommendations.tasks.bulk_refresh_stale_recommendations",
        "schedule": timedelta(days=2),  # Every 2 days
        "options": {"priority": 6}
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

if __name__ == '__main__':
    app.start()
