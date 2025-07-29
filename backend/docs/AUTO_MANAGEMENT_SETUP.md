# Auto-Management System for Large User Base

## Overview

Khi hệ thống có 100+ users, cần có background tasks tự động để:

- Refresh recommendations cho users
- Update user similarities cho collaborative filtering
- Refresh demographic clusters
- Optimize recommendation weights

## Manual Testing

```bash
cd backend

# Xem system status và recommendations
python manage.py auto_manage_system

# Test run ngay (synchronous)
python manage.py auto_manage_system --run-now

# Schedule task (cần Celery worker)
python manage.py auto_manage_system --schedule
```

## Production Setup

### 1. Update Celery Beat Configuration

Add to `backend/config/celery.py`:

```python
from celery.schedules import crontab

# Celery Beat Settings
CELERY_BEAT_SCHEDULE = {
    # Auto-management every 6 hours
    'auto-manage-large-user-base': {
        'task': 'apps.recommendations.tasks.auto_manage_large_user_base',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },

    # Optional: Direct bulk refresh every 12 hours for safety
    'bulk-refresh-stale-recommendations': {
        'task': 'apps.recommendations.tasks.bulk_refresh_stale_recommendations',
        'schedule': crontab(minute=30, hour='*/12'),  # Every 12 hours at :30
    },

    # Optional: Weekly demographic cluster refresh
    'refresh-demographic-clusters': {
        'task': 'apps.recommendations.tasks.refresh_demographic_clusters',
        'schedule': crontab(minute=0, hour=2, day_of_week=1),  # Monday 2AM
    },
}

CELERY_TIMEZONE = 'UTC'
```

### 2. Start Celery Beat Service

```bash
# Development
celery -A config beat -l info

# Production with systemd service
sudo systemctl start celery-beat
sudo systemctl enable celery-beat
```

### 3. Monitor Auto-Management

```bash
# Check logs
tail -f /var/log/celery/beat.log
tail -f /var/log/celery/worker.log

# Manual trigger for testing
python manage.py auto_manage_system --schedule
```

## Task Behavior by User Count

### Small System (< 50 users)

- **Minimal task scheduling**
- Only ensures new users get recommendations
- Runs: `bulk_refresh_stale_recommendations` if needed

### Medium System (50-99 users)

- **Basic task scheduling**
- Runs: `bulk_refresh_stale_recommendations` if 10+ users need recs

### Large System (100+ users)

- **Advanced task scheduling**
- Runs: `bulk_refresh_stale_recommendations`
- Runs: `update_user_similarities_bulk` (if 50+ active users)
- Runs: `refresh_demographic_clusters` (every 500 new users)
- Runs: `optimize_recommendation_weights`

## Background Tasks

### 1. `auto_manage_large_user_base`

- **Main orchestrator task**
- Analyzes system scale and decides what tasks to run
- Logs system status and scheduled tasks

### 2. `bulk_refresh_stale_recommendations`

- **Core recommendation refresh**
- Processes 200 users per batch
- Uses best algorithm per user (collaborative/demographic/hybrid/popular)
- Safe fallback to popular movies

### 3. `update_user_similarities_bulk`

- **Collaborative filtering optimization**
- Processes 100 users per batch
- Updates user similarity matrices
- Requires users with 3+ ratings

## Performance Considerations

### Batch Processing

- Users processed in batches (50-200 per batch)
- Progress logging every 50 users
- Error isolation per user

### Resource Management

- Tasks limit processing to prevent overload
- Staggered scheduling (6h for main, 12h for safety)
- Database query optimization

### Error Handling

- Individual user errors don't stop batch
- Comprehensive logging
- Graceful fallbacks

## Monitoring & Alerts

### Key Metrics to Monitor

```python
# Users needing recommendations
users_needing_recs = User.objects.exclude(
    recommendations__created_at__gte=timezone.now() - timedelta(hours=24)
).distinct().count()

# Recommendation freshness
recent_recs = RecommendationResult.objects.filter(
    created_at__gte=timezone.now() - timedelta(hours=24)
).count()

# System scale
total_users = User.objects.count()
active_users = User.objects.filter(
    last_login__gte=timezone.now() - timedelta(days=7)
).count()
```

### Alert Thresholds

- **Critical**: >20% users without recommendations
- **Warning**: No recommendations generated in 24h despite active users
- **Info**: System scale changes (50→100 users)

## Manual Intervention

### Emergency Fix All Users

```bash
python manage.py fix_user_recommendations --all-users
```

### Test Specific User

```bash
python manage.py test_recommendations --user-id 123
```

### Force System Analysis

```bash
python manage.py auto_manage_system --run-now
```

## Troubleshooting

### No Tasks Running

1. Check Celery worker: `celery -A config worker -l info`
2. Check Celery beat: `celery -A config beat -l info`
3. Verify task imports in `config/celery.py`

### High Resource Usage

1. Reduce batch sizes in tasks
2. Increase task intervals (6h → 12h)
3. Monitor database query performance

### Poor Recommendations

1. Check movie database: `python manage.py list_users`
2. Verify recommendation algorithms
3. Check demographic cluster assignments

## Configuration Options

### Task Intervals

```python
# Conservative (low resources)
'schedule': crontab(minute=0, hour='*/12'),  # Every 12 hours

# Standard (recommended)
'schedule': crontab(minute=0, hour='*/6'),   # Every 6 hours

# Aggressive (high activity)
'schedule': crontab(minute=0, hour='*/3'),   # Every 3 hours
```

### Batch Sizes

```python
# In tasks.py, adjust these based on your system:
users_needing_refresh = User.objects...[:200]  # Reduce to 100 for smaller systems
users_with_ratings = User.objects...[:100]     # Reduce to 50 for smaller systems
```
