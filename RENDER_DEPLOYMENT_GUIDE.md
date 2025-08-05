# Hướng dẫn Deploy Background Worker với Render

## Tổng quan

Dự án Movie Recommendation System sử dụng Celery làm background worker để xử lý các task nặng như:

- Sync dữ liệu phim từ IMDB/TMDB
- Tính toán recommendation algorithms
- Xử lý user interactions
- Cập nhật quality metrics
- Automated scheduling

## Cấu trúc Background Worker

### 1. Celery Configuration

- **File chính**: `backend/config/celery.py`
- **Production config**: `backend/config/celery_production.py`
- **Settings**: `backend/config/settings/prod.py`

### 2. Task Modules

- **Movies**: `backend/apps/movies/tasks.py` (20+ tasks)
- **Recommendations**: `backend/apps/recommendations/tasks.py`
- **Users**: `backend/apps/users/tasks.py`

### 3. Scheduled Tasks

- Movie sync: Weekly/Daily
- Cache updates: Every 30 minutes
- User interactions: Hourly
- Quality metrics: Daily
- Recommendations: Every 4-12 hours

## Bước 1: Chuẩn bị Environment Variables

### Required Environment Variables

```bash
# Database
POSTGRES_DB=movie_mate_db
POSTGRES_USER=movie_mate_user
POSTGRES_PASSWORD=<your_password>
POSTGRES_HOST=<render_db_host>
POSTGRES_PORT=5432

# Redis (Celery Broker)
REDIS_URL=redis://<render_redis_url>
CELERY_BROKER_URL=redis://<render_redis_url>
CELERY_RESULT_BACKEND=redis://<render_redis_url>

# Django
DJANGO_ENV=production
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<generated_key>
DEBUG=false

# External APIs
IMDB_API_KEY=<your_imdb_api_key>
ELASTICSEARCH_CLOUD_URL=<your_elasticsearch_url>
ELASTICSEARCH_USERNAME=<your_elasticsearch_username>
ELASTICSEARCH_PASSWORD=<your_elasticsearch_password>

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=<your_email>
EMAIL_HOST_PASSWORD=<your_app_password>
```

## Bước 2: Deploy với Render

### 2.1 Sử dụng Blueprint (render.yaml)

File `backend/render.yaml` đã được cấu hình với:

```yaml
services:
  # Background Worker
  - type: worker
    name: movie-mate-background-worker
    runtime: python
    rootDir: backend
    plan: starter
    buildCommand: |
      pip install -r requirements/prod.txt
    startCommand: |
      celery -A config worker --loglevel=info --concurrency=2

  # Celery Beat Scheduler
  - type: worker
    name: movie-mate-celery-beat
    runtime: python
    rootDir: backend
    plan: starter
    buildCommand: |
      pip install -r requirements/prod.txt
    startCommand: |
      celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 2.2 Deploy Steps

1. **Push code lên GitHub**:

   ```bash
   git add .
   git commit -m "Add background worker configuration for Render"
   git push origin main
   ```

2. **Connect với Render**:

   - Vào [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect GitHub repository
   - Render sẽ tự động detect `render.yaml`

3. **Configure Environment Variables**:
   - Trong Render Dashboard, vào từng service
   - Set các environment variables cần thiết
   - Đặc biệt chú ý: `IMDB_API_KEY`, `ELASTICSEARCH_*`, `EMAIL_*`

## Bước 3: Monitoring và Logs

### 3.1 Render Dashboard

- **Logs**: Xem real-time logs trong Render Dashboard
- **Metrics**: Monitor CPU, Memory usage
- **Health Checks**: Automatic health monitoring

### 3.2 Celery Monitoring

```bash
# Check worker status
celery -A config inspect active

# Check scheduled tasks
celery -A config inspect scheduled

# Check registered tasks
celery -A config inspect registered
```

### 3.3 Log Monitoring

```bash
# View worker logs
celery -A config worker --loglevel=debug

# View beat logs
celery -A config beat --loglevel=debug
```

## Bước 4: Production Optimizations

### 4.1 Worker Configuration

```python
# backend/config/celery_production.py
app.conf.update(
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    task_time_limit=3600,
    task_soft_time_limit=3000,
)
```

### 4.2 Task Scheduling (Production)

- **Less frequent syncs**: Weekly instead of daily
- **Batch processing**: Smaller batch sizes
- **Resource optimization**: Reduced concurrency

### 4.3 Error Handling

```python
@shared_task(bind=True, max_retries=3)
def sync_popular_movies(self):
    try:
        # Task logic
        pass
    except Exception as exc:
        self.retry(countdown=60, exc=exc)
```

## Bước 5: Troubleshooting

### 5.1 Common Issues

**Worker không start**:

```bash
# Check Redis connection
celery -A config inspect ping

# Check database connection
python manage.py dbshell
```

**Tasks không chạy**:

```bash
# Check task queue
celery -A config inspect active_queues

# Check registered tasks
celery -A config inspect registered
```

**Memory issues**:

```bash
# Reduce concurrency
celery -A config worker --concurrency=1

# Increase max tasks per child
celery -A config worker --max-tasks-per-child=500
```

### 5.2 Debug Commands

```bash
# Test task execution
celery -A config call apps.movies.tasks.sync_popular_movies

# Check worker stats
celery -A config inspect stats

# Purge task queue
celery -A config purge
```

## Bước 6: Scaling

### 6.1 Horizontal Scaling

- Tăng số lượng worker instances
- Sử dụng different queues cho different task types
- Load balancing across workers

### 6.2 Vertical Scaling

- Upgrade Render plan (starter → pro)
- Increase memory allocation
- Optimize task execution

### 6.3 Queue Management

```python
# Priority queues
CELERY_TASK_ROUTES = {
    'apps.movies.tasks.sync_popular_movies': {'queue': 'high_priority'},
    'apps.movies.tasks.calculate_quality_metrics': {'queue': 'low_priority'},
}
```

## Bước 7: Backup và Recovery

### 7.1 Database Backup

```bash
# Render tự động backup PostgreSQL
# Manual backup
pg_dump $DATABASE_URL > backup.sql
```

### 7.2 Task Recovery

```python
# Persistent task results
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_EXPIRES = 3600
```

## Kết luận

Background worker đã được cấu hình để chạy trên Render với:

- **2 Worker services**: Background tasks + Scheduled tasks
- **Production optimizations**: Reduced frequency, optimized resources
- **Monitoring**: Render dashboard + Celery monitoring
- **Scalability**: Easy horizontal/vertical scaling
- **Reliability**: Error handling, retries, health checks

Sau khi deploy, hệ thống sẽ tự động:

- Sync dữ liệu phim định kỳ
- Tính toán recommendations cho users
- Cập nhật quality metrics
- Xử lý user interactions
- Maintain system health
