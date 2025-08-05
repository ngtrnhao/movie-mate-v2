# Hướng dẫn Set Thời gian cho Task trong Production

## 📅 Tổng quan về Task Scheduling

Dự án Movie Recommendation System sử dụng **Celery Beat** để schedule các task tự động. Có **2 nơi chính** để cấu hình thời gian:

### 1. **File chính**: `backend/config/celery_production.py`

- Cấu hình scheduling cho production environment
- Sử dụng `crontab` và `timedelta` để set thời gian chính xác

### 2. **File development**: `backend/config/celery.py`

- Cấu hình scheduling cho development environment
- Sử dụng `timedelta` cho testing

## 🕐 Cách Set Thời gian cho Task

### A. Sử dụng `crontab` (Khuyến nghị cho Production)

```python
from celery.schedules import crontab

# Ví dụ: Chạy task vào 2 AM mỗi Chủ nhật
"sync_popular_movies": {
    "task": "apps.movies.tasks.sync_popular_movies",
    "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM
    "options": {"priority": 8}
}
```

#### Cú pháp `crontab`:

```python
crontab(
    minute=0,           # 0-59, default=0
    hour=2,             # 0-23, default=0
    day_of_week=0,      # 0-6 (Sunday=0), default=*
    day_of_month=1,     # 1-31, default=*
    month_of_year=1,    # 1-12, default=*
)
```

#### Ví dụ thời gian:

```python
# Mỗi giờ
crontab(minute=0)

# Mỗi 4 giờ
crontab(hour="*/4", minute=0)

# 6 AM và 6 PM mỗi ngày
crontab(hour="6,18", minute=0)

# Mỗi Chủ nhật 2 AM
crontab(hour=2, minute=0, day_of_week=0)

# Mỗi 3 ngày lúc 2 AM
crontab(hour=2, minute=0, day_of_month="*/3")
```

### B. Sử dụng `timedelta` (Đơn giản)

```python
from datetime import timedelta

# Ví dụ: Chạy task mỗi 30 phút
"update_movie_cache": {
    "task": "apps.movies.tasks.update_movie_cache",
    "schedule": timedelta(minutes=30),
    "options": {"priority": 6}
}
```

## 📋 Danh sách Task và Thời gian đề xuất

### 🎬 Movie Sync Tasks

```python
# Sync popular movies - Weekly (Sunday 2 AM)
"sync_popular_movies": {
    "task": "apps.movies.tasks.sync_popular_movies",
    "schedule": crontab(hour=2, minute=0, day_of_week=0),
    "options": {"priority": 8}
}

# Sync top rated movies - Weekly (Monday 3 AM)
"sync_top_rated_movies": {
    "task": "apps.movies.tasks.sync_top_rated_movies",
    "schedule": crontab(hour=3, minute=0, day_of_week=1),
    "options": {"priority": 8}
}

# Sync upcoming movies - Every 3 days (2 AM)
"sync_upcoming_movies": {
    "task": "apps.movies.tasks.sync_upcoming_movies",
    "schedule": crontab(hour=2, minute=0, day_of_month="*/3"),
    "options": {"priority": 7}
}
```

### 💾 Cache Update Tasks

```python
# Update movie cache - Every 30 minutes
"update_movie_cache": {
    "task": "apps.movies.tasks.update_movie_cache",
    "schedule": timedelta(minutes=30),
    "options": {"priority": 6}
}

# Refresh genre summary - Twice daily (6 AM and 6 PM)
"refresh_genre_summary": {
    "task": "apps.metadata.tasks.refresh_genre_summary_task",
    "schedule": crontab(hour="6,18", minute=0),
    "options": {"priority": 5}
}
```

### 👥 User Interaction Tasks

```python
# Process user interactions - Hourly
"process_user_interactions_frequent": {
    "task": "apps.movies.tasks.process_user_interactions_auto",
    "schedule": crontab(minute=0),
    "kwargs": {"hours": 2},
    "options": {"priority": 7}
}

# Process user interactions - Every 4 hours
"process_user_interactions_hourly": {
    "task": "apps.movies.tasks.process_user_interactions_auto",
    "schedule": crontab(hour="*/4", minute=30),
    "kwargs": {"hours": 1},
    "options": {"priority": 6}
}
```

### 🎯 Recommendation Tasks

```python
# Update user similarities - Twice daily (8 AM and 8 PM)
"update_user_similarities": {
    "task": "apps.users.tasks.update_user_similarities_batch",
    "schedule": crontab(hour="8,20", minute=0),
    "options": {"priority": 7}
}

# Generate recommendations - Every 4 hours
"generate_recommendations_active_users": {
    "task": "apps.users.tasks.generate_recommendations_for_active_users",
    "schedule": crontab(hour="*/4", minute=10),
    "options": {"priority": 8}
}
```

### 🔧 Quality Metrics Tasks

```python
# Calculate quality for new movies - Every 6 hours
"calculate_quality_new_movies": {
    "task": "apps.movies.tasks.calculate_quality_metrics_auto",
    "schedule": crontab(hour="*/6", minute=20),
    "kwargs": {"target_type": "new", "batch_size": 20, "max_movies": 50},
    "options": {"priority": 6}
}

# Calculate quality for low quality movies - Daily (4 AM)
"calculate_quality_low_quality": {
    "task": "apps.movies.tasks.calculate_quality_metrics_auto",
    "schedule": crontab(hour=4, minute=0),
    "kwargs": {"target_type": "low_quality", "batch_size": 15, "max_movies": 30},
    "options": {"priority": 4}
}
```

### 🧹 Cleanup Tasks

```python
# Cleanup expired recommendations - Daily (7 AM)
"cleanup_expired_recommendations": {
    "task": "apps.recommendations.tasks.cleanup_expired_recommendations",
    "schedule": crontab(hour=7, minute=0),
    "options": {"priority": 3}
}
```

## ⚙️ Cách Tùy chỉnh Thời gian

### 1. Thay đổi thời gian trong `celery_production.py`

```python
# Ví dụ: Thay đổi sync popular movies từ weekly sang daily
"sync_popular_movies": {
    "task": "apps.movies.tasks.sync_popular_movies",
    "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    "options": {"priority": 8}
}

# Ví dụ: Thay đổi cache update từ 30 phút sang 15 phút
"update_movie_cache": {
    "task": "apps.movies.tasks.update_movie_cache",
    "schedule": timedelta(minutes=15),  # Every 15 minutes
    "options": {"priority": 6}
}
```

### 2. Thêm Task mới

```python
# Thêm task mới vào beat_schedule
"my_new_task": {
    "task": "apps.myapp.tasks.my_new_task",
    "schedule": crontab(hour=12, minute=0),  # Daily at 12 PM
    "options": {"priority": 5}
}
```

### 3. Tạm thời disable Task

```python
# Comment out task để disable
# "sync_popular_movies": {
#     "task": "apps.movies.tasks.sync_popular_movies",
#     "schedule": crontab(hour=2, minute=0, day_of_week=0),
#     "options": {"priority": 8}
# },
```

## 🎯 Priority Levels

```python
# Priority levels (0-9, 9 = highest priority)
"options": {"priority": 9}  # Highest priority (scheduled actions)
"options": {"priority": 8}  # High priority (movie sync, recommendations)
"options": {"priority": 7}  # Medium-high (user interactions, similarities)
"options": {"priority": 6}  # Medium (cache updates, quality metrics)
"options": {"priority": 5}  # Medium-low (genre summary, scheduling status)
"options": {"priority": 4}  # Low (quality maintenance)
"options": {"priority": 3}  # Very low (cleanup tasks)
"options": {"priority": 2}  # Lowest (maintenance tasks)
```

## 🔄 Deploy Changes

### 1. Sau khi thay đổi scheduling:

```bash
# Restart Celery Beat service
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Hoặc restart worker service
celery -A config worker --loglevel=info --concurrency=2
```

### 2. Kiểm tra scheduled tasks:

```bash
# View scheduled tasks
celery -A config inspect scheduled

# View beat schedule
celery -A config beat --loglevel=info
```

## 📊 Monitoring Task Execution

### 1. Check task logs:

```bash
# View worker logs
celery -A config worker --loglevel=debug

# View beat logs
celery -A config beat --loglevel=debug
```

### 2. Check task status:

```bash
# Check active tasks
celery -A config inspect active

# Check task statistics
celery -A config inspect stats
```

## ⚠️ Lưu ý quan trọng

### 1. **Time Zone**

- Tất cả thời gian đều theo **UTC**
- Nếu muốn theo timezone khác, cần cấu hình trong settings

### 2. **Resource Management**

- **High frequency tasks** (mỗi 15-30 phút): Cache updates
- **Medium frequency tasks** (mỗi 1-6 giờ): User interactions, recommendations
- **Low frequency tasks** (daily/weekly): Movie sync, quality metrics

### 3. **Error Handling**

- Tasks có `max_retries` và `time_limit`
- Failed tasks sẽ được retry tự động
- Check logs để monitor errors

### 4. **Performance Optimization**

- **Batch size**: Giảm batch size cho tasks nặng
- **Concurrency**: Tăng worker concurrency nếu cần
- **Priority**: Set priority phù hợp cho từng task

## 🎯 Best Practices

1. **Spread out heavy tasks**: Không chạy nhiều task nặng cùng lúc
2. **Use off-peak hours**: Chạy task nặng vào giờ ít traffic (2-6 AM)
3. **Monitor resource usage**: Check CPU, memory usage
4. **Test scheduling**: Test trên development trước khi deploy
5. **Document changes**: Ghi chú khi thay đổi scheduling

## 📝 Ví dụ Cấu hình Production

```python
# Production-optimized scheduling
app.conf.beat_schedule = {
    # Light tasks - High frequency
    "update_movie_cache": {
        "task": "apps.movies.tasks.update_movie_cache",
        "schedule": timedelta(minutes=30),
        "options": {"priority": 6}
    },

    # Medium tasks - Medium frequency
    "process_user_interactions": {
        "task": "apps.movies.tasks.process_user_interactions_auto",
        "schedule": crontab(hour="*/2", minute=0),  # Every 2 hours
        "options": {"priority": 7}
    },

    # Heavy tasks - Low frequency (off-peak hours)
    "sync_popular_movies": {
        "task": "apps.movies.tasks.sync_popular_movies",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM
        "options": {"priority": 8}
    },

    # Maintenance tasks - Very low frequency
    "cleanup_expired_recommendations": {
        "task": "apps.recommendations.tasks.cleanup_expired_recommendations",
        "schedule": crontab(hour=7, minute=0),  # Daily 7 AM
        "options": {"priority": 3}
    },
}
```
