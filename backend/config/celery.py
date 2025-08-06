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
        "schedule": timedelta(days=5),
    },
    "sync_top_rated_movies": {
        "task": "apps.movies.tasks.sync_top_rated_movies",
        "schedule": timedelta(days=5),
    },
    "sync_upcoming_movies": {
        "task": "apps.movies.tasks.sync_upcoming_movies",
        "schedule": timedelta(days=5),
    },
    "update_movie_cache": {
        "task": "apps.movies.tasks.update_movie_cache",
        "schedule": timedelta(minutes=10),
    },
    "refresh_genre_summary": {
        "task": "apps.metadata.tasks.refresh_genre_summary_task",
        "schedule": timedelta(hours=6),
    },

    # Auto-processing tasks
    "process_user_interactions_frequent": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": timedelta(minutes=15),
        "kwargs": {"hours": 1}
    },
    "process_user_interactions_hourly": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": timedelta(hours=0.25),
        "kwargs": {"hours": 1}
    },
    "sync_trending_categories": {
        "task": "apps.movies.tasks.sync_trending_categories_auto",
        "schedule": timedelta(minutes=15),
    },

    # Scheduling automation tasks
    "process_scheduled_actions": {
        "task": "apps.movies.tasks.process_scheduled_actions_auto",
        "schedule": timedelta(minutes=5),
        "options": {"priority": 9}
    },
    "update_scheduling_status": {
        "task": "apps.movies.tasks.update_scheduling_status_auto",
        "schedule": timedelta(hours=1),
        "options": {"priority": 5}
    },

    # Quality automation tasks
    "calculate_quality_new_movies": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(hours=2),
        "kwargs": {"target_type": "new", "batch_size": 25, "max_movies": 100},
        "options": {"priority": 6}
    },
    "calculate_quality_low_quality": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(hours=12),
        "kwargs": {"target_type": "low_quality", "batch_size": 20, "max_movies": 50},
        "options": {"priority": 4}
    },
    "calculate_quality_outdated": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": timedelta(days=1),
        "kwargs": {"target_type": "outdated", "batch_size": 30, "max_movies": 200},
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
        "schedule": timedelta(hours=6),
        "options": {"priority": 7}
    },
    "generate_recommendations_active_users": {
        "task": "apps.users.tasks.generate_recommendations_for_active_users",
        "schedule": timedelta(hours=2),
        "options": {"priority": 8}
    },

    # ===== NEW BACKGROUND RECOMMENDATION TASKS =====
    # Background collaborative filtering for stale recommendations (batch)
    "background_collaborative_refresh": {
        "task": "apps.recommendations.tasks.batch_generate_collaborative_recommendations",
        "schedule": timedelta(hours=4),
        "options": {"priority": 6}
    },
    # Background hybrid recommendations for stale recommendations (batch)
    "background_hybrid_refresh": {
        "task": "apps.recommendations.tasks.batch_generate_hybrid_recommendations",
        "schedule": timedelta(hours=4),
        "options": {"priority": 6}
    },
    # Background demographic recommendations for stale recommendations (batch)
    "background_demographic_refresh": {
        "task": "apps.recommendations.tasks.batch_generate_demographic_recommendations",
        "schedule": timedelta(hours=6),
        "options": {"priority": 5}
    },
    # Refresh all recommendation types for active users
    "refresh_all_recommendations_batch": {
        "task": "apps.recommendations.tasks.refresh_all_recommendations_async",
        "schedule": timedelta(hours=8),
        "options": {"priority": 7}
    },
    # "refresh_demographic_clusters": {
    #     "task": "apps.recommendations.tasks.refresh_demographic_clusters",
    #     "schedule": timedelta(days=1),
    #     "options": {"priority": 5}
    # },
    "cleanup_expired_recommendations": {
        "task": "apps.recommendations.tasks.cleanup_expired_recommendations",
        "schedule": timedelta(hours=12),
        "options": {"priority": 3}
    },

    # Auto-management for large user bases (100+ users)
    "auto_manage_large_user_base": {
        "task": "apps.recommendations.tasks.auto_manage_large_user_base",
        "schedule": timedelta(hours=6),
        "options": {"priority": 8}
    },

    # Bulk recommendation refresh (triggered by auto-management)
    "bulk_refresh_stale_recommendations_weekly": {
        "task": "apps.recommendations.tasks.bulk_refresh_stale_recommendations",
        "schedule": timedelta(days=1),
        "options": {"priority": 6}
    },
}

# Task time limits are now configured in Django settings
# CELERY_TASK_TIME_LIMIT and CELERY_TASK_SOFT_TIME_LIMIT

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request:{self.request!r}')
