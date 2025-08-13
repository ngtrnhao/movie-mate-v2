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
    # ===== MOVIE SYNC TASKS =====
    # Sync popular movies weekly (Sunday 2 AM)
    "sync_popular_movies": {
        "task": "apps.movies.tasks.sync_popular_movies",
        # "schedule": crontab(hour=1, minute=0, day_of_week="*/5"),  # every 5 days
        "schedule": timedelta(minutes=30),
        "options": {"priority": 10}
    },
    # Sync top rated movies weekly (Monday 3 AM)
    "sync_top_rated_movies": {
        "task": "apps.movies.tasks.sync_top_rated_movies",
        "schedule": timedelta(minutes=30),
        "options": {"priority": 10}
    },
    # Sync upcoming movies every 3 days (2 AM)
    "sync_upcoming_movies": {
        "task": "apps.movies.tasks.sync_upcoming_movies",
        "schedule": timedelta(minutes=30),
        "options": {"priority": 10}
    },

    # ===== CACHE UPDATE TASKS =====
    # Update movie cache every 30 minutes
    "update_movie_cache": {
        "task": "apps.movies.tasks.update_movie_cache",
        "schedule": timedelta(minutes=30),
        "options": {"priority": 6}
    },
    # Refresh genre summary twice daily (6 AM and 6 PM)
    "refresh_genre_summary": {
        "task": "apps.metadata.tasks.refresh_genre_summary_task",
        "schedule": crontab(hour="6,18", minute=0),  # 6 AM and 6 PM
        "options": {"priority": 5}
    },

    # ===== USER INTERACTION PROCESSING =====
    # Process user interactions hourly
    "process_user_interactions_frequent": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
        "kwargs": {"hours": 2},
        "options": {"priority": 7}
    },
    # Process user interactions every 4 hours
    "process_user_interactions_hourly": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": crontab(hour="*/4", minute=30),  # Every 4 hours at minute 30
        "kwargs": {"hours": 1},
        "options": {"priority": 6}
    },

    # ===== TRENDING CATEGORIES =====
    # Sync trending categories every 6 hours
    "sync_trending_categories": {
        "task": "apps.movies.tasks.sync_trending_categories_auto",
        "schedule": crontab(hour="*/6", minute=15),  # Every 6 hours at minute 15
        "options": {"priority": 6}
    },

    # ===== SCHEDULING AUTOMATION =====
    # Process scheduled actions every 15 minutes
    "process_scheduled_actions": {
        "task": "apps.movies.tasks.process_scheduled_actions_auto",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "options": {"priority": 9}
    },
    # Update scheduling status every 2 hours
    "update_scheduling_status": {
        "task": "apps.movies.tasks.update_scheduling_status_auto",
        "schedule": crontab(hour="*/2", minute=45),  # Every 2 hours at minute 45
        "options": {"priority": 5}
    },

    # ===== QUALITY METRICS =====
    # Calculate quality for new movies every 6 hours
    "calculate_quality_new_movies": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": crontab(hour="*/6", minute=20),  # Every 6 hours at minute 20
        "kwargs": {"target_type": "new", "batch_size": 20, "max_movies": 50},
        "options": {"priority": 6}
    },
    # Calculate quality for low quality movies daily
    "calculate_quality_low_quality": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
        "kwargs": {"target_type": "low_quality", "batch_size": 15, "max_movies": 30},
        "options": {"priority": 4}
    },
    # Calculate quality for outdated movies every 2 days
    "calculate_quality_outdated": {
        "task": "apps.movies.tasks.calculate_quality_metrics_auto",
        "schedule": crontab(hour=5, minute=0, day_of_month="*/2"),  # Every 2 days at 5 AM
        "kwargs": {"target_type": "outdated", "batch_size": 25, "max_movies": 100},
        "options": {"priority": 3}
    },
    # Quality maintenance daily
    "quality_maintenance": {
        "task": "apps.movies.tasks.quality_maintenance_auto",
        "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM
        "options": {"priority": 2}
    },

    # ===== RECOMMENDATION SYSTEM =====
    # Update user similarities twice daily (8 AM and 8 PM)
    "update_user_similarities": {
        "task": "apps.users.tasks.update_user_similarities_batch",
        "schedule": crontab(hour="8,20", minute=0),  # 8 AM and 8 PM
        "options": {"priority": 7}
    },
    # Generate recommendations for active users every 4 hours
    "generate_recommendations_active_users": {
        "task": "apps.users.tasks.generate_recommendations_for_active_users",
        "schedule": crontab(hour="*/4", minute=10),  # Every 4 hours at minute 10
        "options": {"priority": 8}
    },

    # ===== NEW BACKGROUND RECOMMENDATION TASKS =====
    # Background collaborative filtering every 6 hours (batch)
    "background_collaborative_refresh": {
        "task": "apps.recommendations.tasks.batch_generate_collaborative_recommendations",
        "schedule": crontab(hour="*/6", minute=5),  # Every 6 hours at minute 5
        "options": {"priority": 6}
    },
    # Background hybrid recommendations every 6 hours (batch)
    "background_hybrid_refresh": {
        "task": "apps.recommendations.tasks.batch_generate_hybrid_recommendations",
        "schedule": crontab(hour="*/6", minute=15),  # Every 6 hours at minute 15
        "options": {"priority": 6}
    },
    # Background demographic recommendations every 8 hours (batch)
    "background_demographic_refresh": {
        "task": "apps.recommendations.tasks.batch_generate_demographic_recommendations",
        "schedule": crontab(hour="*/8", minute=25),  # Every 8 hours at minute 25
        "options": {"priority": 5}
    },
    # Refresh all recommendation types daily
    "refresh_all_recommendations_batch": {
        "task": "apps.recommendations.tasks.refresh_all_recommendations_async",
        "schedule": crontab(hour=11, minute=0),  # Daily at 11 AM
        "options": {"priority": 7}
    },

    # ===== CLEANUP TASKS =====
    # Cleanup expired recommendations daily
    "cleanup_expired_recommendations": {
        "task": "apps.recommendations.tasks.cleanup_expired_recommendations",
        "schedule": crontab(hour=7, minute=0),  # Daily at 7 AM
        "options": {"priority": 3}
    },

    # ===== AUTO-MANAGEMENT =====
    # Auto-manage large user base twice daily
    "auto_manage_large_user_base": {
        "task": "apps.recommendations.tasks.auto_manage_large_user_base",
        "schedule": crontab(hour="9,21", minute=0),  # 9 AM and 9 PM
        "options": {"priority": 8}
    },

    # ===== BULK REFRESH =====
    # Bulk refresh stale recommendations every 2 days
    "bulk_refresh_stale_recommendations_weekly": {
        "task": "apps.recommendations.tasks.bulk_refresh_stale_recommendations",
        "schedule": crontab(hour=10, minute=0, day_of_month="*/2"),  # Every 2 days at 10 AM
        "options": {"priority": 6}
    },

    # ===== PURE CF OPTIMIZATION TASKS =====
    # Detect and generate missing CF recommendations every 4 hours
    "detect_missing_cf_recommendations": {
        "task": "apps.recommendations.tasks.detect_and_generate_missing_cf_recommendations",
        "schedule": crontab(hour="*/4", minute=35),  # Every 4 hours at minute 35
        "options": {"priority": 7}
    },
    # Smart CF prioritization daily at 1 AM
    "smart_cf_prioritization": {
        "task": "apps.recommendations.tasks.smart_cf_recommendation_prioritization",
        "schedule": crontab(hour=1, minute=30),  # Daily at 1:30 AM
        "options": {"priority": 8}
    },
    # Precompute user similarities daily at 2 AM
    "precompute_similarities": {
        "task": "apps.recommendations.tasks.precompute_user_similarities_batch",
        "schedule": crontab(hour=2, minute=30),  # Daily at 2:30 AM
        "options": {"priority": 7}
    },
    # Monitor CF system health three times daily (6 AM, 2 PM, 10 PM)
    "monitor_cf_health": {
        "task": "apps.recommendations.tasks.monitor_cf_system_health",
        "schedule": crontab(hour="6,14,22", minute=45),  # 6 AM, 2 PM, 10 PM
        "options": {"priority": 5}
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

if __name__ == '__main__':
    app.start()
