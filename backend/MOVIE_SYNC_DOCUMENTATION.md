# 🎬 HỆ THỐNG SYNC MOVIE - DOCUMENTATION

## 📋 TỔNG QUAN HỆ THỐNG

### 🎯 Mục Đích

Hệ thống sync movie tự động cập nhật dữ liệu phim từ IMDB API để phục vụ các tab:

- **🔥 Trending Movies** (Popular)
- **⭐ Top Rated Movies**
- **🎬 Upcoming Movies**

### 🔧 Technology Stack

- **Backend:** Django + PostgreSQL + Redis
- **Task Queue:** Celery + Celery Beat
- **External API:** IMDB RapidAPI
- **Caching:** Redis (API cache + Movie data cache)
- **Frontend:** React (Movie display)

### ⏰ Lịch Trình Hoạt Động

- **Frequency:** Mỗi 7 ngày tự động
- **Parallel Processing:** 3 tasks chạy đồng thời
- **Rate Limiting:** 2 giây giữa mỗi API call
- **Cache Duration:** 5 phút (API), 24 giờ (Movie data)

---

## 🔄 SƠ ĐỒ QUY TRÌNH CHÍNH

### Main Process Flow

```mermaid
flowchart TD
    A["🕒 Celery Beat Scheduler<br/>Mỗi 7 ngày"] --> B["🎯 Trigger 3 Tasks Parallel"]

    B --> C1["sync_popular_movies()"]
    B --> C2["sync_top_rated_movies()"]
    B --> C3["sync_upcoming_movies()"]

    C1 --> D1["📡 IMDB API<br/>/get-most-popular-movies<br/>limit=50"]
    C2 --> D2["📡 IMDB API<br/>/get-top-rated-movies<br/>limit=50"]
    C3 --> D3["📡 IMDB API<br/>/get-coming-soon-movies<br/>limit=50"]

    D1 --> E["📋 Get Movie IDs List<br/>['tt1234567', 'tt2345678', ...]"]
    D2 --> E
    D3 --> E

    E --> F["🔄 For Each IMDB ID"]
    F --> G["🧹 Clean & Validate<br/>Extract tt1234567"]
    G --> H{"✅ Valid Format?"}

    H -->|❌ No| I["⚠️ Log Error & Skip"]
    H -->|✅ Yes| J["🔍 Get or Create Movie"]

    J --> K["🏷️ Set Category Flags<br/>is_popular/is_top_rated/is_upcoming"]
    K --> L["💾 Quick Save to DB"]
    L --> M["📋 Queue Detail Task<br/>process_movie_data.delay()"]
    M --> N["⏱️ Rate Limit Sleep (2s)"]

    N --> O{"📝 More Movies?"}
    O -->|✅ Yes| F
    O -->|❌ No| P["🎉 Task Complete<br/>Log Summary"]

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style P fill:#e8f5e8
```

### Detail Processing Sub-Flow

```mermaid
flowchart TD
    A["📋 process_movie_data.delay(imdb_id)"] --> B["🔍 Get Movie from DB"]

    B --> C["📡 IMDB API Calls (Parallel)"]
    C --> D1["🎬 Get Movie Details<br/>title, poster, runtime"]
    C --> D2["📝 Get English Overview<br/>plot synopsis EN"]
    C --> D3["🇻🇳 Get Vietnamese Overview<br/>plot synopsis VI"]

    D1 --> E["🔄 Map & Validate Data"]
    D2 --> E
    D3 --> E

    E --> F["💾 Update Movie in DB<br/>update_or_create()"]
    F --> G["🗄️ Cache Individual Movie<br/>24h cache"]
    G --> H["📊 Update List Caches<br/>popular_movies:{3,10,20,50,100}"]
    H --> I["🧹 Clear API Cache<br/>imdb_* patterns"]
    I --> J["✅ Task Complete"]

    style A fill:#e1f5fe
    style J fill:#e8f5e8
```

---

## 📋 SEQUENCE DIAGRAM - TƯƠNG TÁC CHI TIẾT

```mermaid
sequenceDiagram
    participant CB as Celery Beat
    participant CW as Celery Worker
    participant IMDB as IMDB API
    participant DB as PostgreSQL
    participant Cache as Redis
    participant API as Django API
    participant FE as React Frontend

    Note over CB: Every 7 days
    CB->>+CW: trigger sync tasks (3 parallel)

    Note over CW: Phase 1: Get Movie Lists
    CW->>+IMDB: GET /get-most-popular-movies
    IMDB-->>-CW: ["tt1234567", "tt2345678"]

    Note over CW: Phase 2: Quick Flag Setting
    loop For each IMDB ID
        CW->>+DB: get_or_create(imdb_id)
        DB-->>-CW: Movie object
        CW->>+DB: set is_popular=True
        DB-->>-CW: saved
        CW->>CW: queue process_movie_data.delay()
        CW->>CW: sleep(2s) # rate limiting
    end

    Note over CW: Phase 3: Async Detail Processing
    par Async Tasks
        CW->>+IMDB: GET /get-details?tconst=tt1234567
        IMDB-->>-CW: {title, poster_url, runtime}

        CW->>+IMDB: GET /get-plots?lang=en-US
        IMDB-->>-CW: {plots: ["English overview"]}

        CW->>+IMDB: GET /get-plots?lang=vi-VN
        IMDB-->>-CW: {plots: ["Vietnamese overview"]}

        CW->>+DB: update_or_create(imdb_id, data)
        DB-->>-CW: Movie with full details

        CW->>+Cache: set movie:tt1234567 (24h)
        Cache-->>-CW: cached
    end

    CW->>+Cache: delete_pattern("imdb_*")
    Cache-->>-CW: API cache cleared
    CW-->>-CB: sync completed

    Note over FE,API: User Requests Movies
    FE->>+API: GET /api/movies/trending/
    API->>+Cache: get('trending_movies')
    Cache-->>-API: cache miss

    API->>+DB: filter(is_popular=True, poster_url__isnull=False)
    DB-->>-API: movies queryset

    API->>API: score by data completeness
    API->>API: sort by score, take top 30
    API->>+Cache: set('trending_movies', 300s)
    Cache-->>-API: cached

    API-->>-FE: {status: "success", data: [...]}
    FE->>FE: render MovieCard components
```

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND      │    │   BACKEND       │    │   EXTERNAL      │
│                 │    │                 │    │                 │
│ React Frontend  │───▶│ Django API      │───▶│ IMDB RapidAPI   │
│ Movie Cards     │    │ REST Endpoints  │    │ Movie Data      │
│ Category Tabs   │    │ /api/movies/*   │    │ Popular/Top/Up  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   TASK QUEUE    │
                    │                 │
                    │ Celery Worker   │◀── Celery Beat (7 days)
                    │ Redis Broker    │
                    │ Async Processing│
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   DATA LAYER    │
                    │                 │
                    │ PostgreSQL DB   │◀── Movie Models
                    │ Redis Cache     │◀── Multi-level Cache
                    │ Movie Ratings   │
                    └─────────────────┘
```

### Key Components

| Component           | Location                               | Chức Năng                  |
| ------------------- | -------------------------------------- | -------------------------- |
| **Celery Schedule** | `config/celery.py`                     | Định nghĩa lịch 7 ngày     |
| **Sync Tasks**      | `apps/movies/tasks.py`                 | Logic sync cho 3 loại phim |
| **IMDB Service**    | `apps/movies/services/imdb_service.py` | Interface với IMDB API     |
| **Movie Models**    | `apps/movies/models.py`                | Schema + business logic    |
| **API Views**       | `apps/movies/views.py`                 | REST endpoints             |
| **Serializers**     | `apps/movies/serializers.py`           | JSON response format       |

---

## 📊 CHI TIẾT TECHNICAL SPECS

### Database Schema - Movie Model

```python
class Movie(models.Model):
    # Identifiers
    imdb_id = models.CharField(max_length=20, unique=True)
    tmdb_id = models.IntegerField(null=True, blank=True)

    # Basic Info
    title = models.CharField(max_length=500)
    title_en = models.CharField(max_length=500, blank=True)
    title_vi = models.CharField(max_length=500, blank=True)

    # Visual Assets
    poster_url = models.URLField(blank=True, null=True)
    backdrop_url = models.URLField(blank=True, null=True)

    # Content
    overview_en = models.TextField(blank=True)
    overview_vi = models.TextField(blank=True)

    # Meta Data
    release_date = models.DateField(blank=True, null=True)
    runtime = models.IntegerField(blank=True, null=True)

    # Category Flags (IMPORTANT!)
    is_popular = models.BooleanField(default=False)      # Trending tab
    is_top_rated = models.BooleanField(default=False)    # Top Rated tab
    is_upcoming = models.BooleanField(default=False)     # Upcoming tab

    # Performance Cache
    cached_imdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    cached_tmdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    combined_rating_score = models.DecimalField(max_digits=3, decimal_places=1, null=True)

    # Sync Tracking
    last_sync = models.DateTimeField(auto_now=True)
    last_imdb_sync = models.DateTimeField(null=True, blank=True)
```

### API Tab Filtering Logic

#### 1. 🔥 Trending Tab (`/api/movies/trending/`)

```python
# Filter conditions
movies = Movie.objects.filter(
    is_popular=True,              # ✅ Must be marked as popular
    poster_url__isnull=False,     # ✅ Must have poster image
).order_by('-release_date')       # 📅 Sort by newest release

# Data completeness scoring (0-9 points)
def calculate_score(movie):
    score = 0
    if movie.poster_url: score += 3      # Visual: poster (high priority)
    if movie.backdrop_url: score += 2    # Visual: backdrop
    if movie.overview_en: score += 2     # Content: English overview
    if movie.overview_vi: score += 1     # Content: Vietnamese overview
    if movie.prefetched_ratings: score += 1  # Meta: ratings
    return score

# Final selection: Top 30 by score
trending_movies = sorted_by_score[:30]
```

#### 2. ⭐ Top Rated Tab (`/api/movies/top-rated/`)

```python
movies = Movie.objects.filter(
    is_top_rated=True,            # ✅ Must be marked as top rated
    poster_url__isnull=False,     # ✅ Must have poster
    cached_imdb_rating__gte=7.0,  # ✅ High rating filter
).order_by('-cached_imdb_rating', '-release_date')  # Sort by rating first
```

#### 3. 🎬 Upcoming Tab (`/api/movies/upcoming/`)

```python
movies = Movie.objects.filter(
    is_upcoming=True,             # ✅ Must be marked as upcoming
    poster_url__isnull=False,     # ✅ Must have poster
    release_date__gte=timezone.now().date(),  # ✅ Future release date
).order_by('release_date')        # 📅 Sort by earliest release
```

### Cache Strategy

#### Redis Cache Keys

```python
# Individual Movie Cache (24 hours)
MOVIE_CACHE_KEY = "movie:{imdb_id}"
cache.set(f"movie:tt1234567", movie_data, 86400)

# List Caches (1 hour)
POPULAR_CACHE_KEYS = [
    "popular_movies:3",    # Top 3 for quick preview
    "popular_movies:10",   # Top 10 for carousel
    "popular_movies:20",   # Top 20 for grid
    "popular_movies:50",   # Top 50 for full page
    "popular_movies:100",  # Top 100 for infinite scroll
]

# API Response Cache (5 minutes)
API_CACHE_KEYS = [
    "trending_movies",     # /api/movies/trending/
    "top_rated_movies",    # /api/movies/top-rated/
    "upcoming_movies",     # /api/movies/upcoming/
]
```

---

## ⚙️ CONFIGURATION

### Celery Beat Schedule

```python
# config/celery.py
app.conf.beat_schedule = {
    "sync_popular_movies": {
        "task": "apps.movies.tasks.sync_popular_movies",
        "schedule": timedelta(days=7),  # Every 7 days
        "options": {"queue": "movies"},
    },
    "sync_top_rated_movies": {
        "task": "apps.movies.tasks.sync_top_rated_movies",
        "schedule": timedelta(days=7),
        "options": {"queue": "movies"},
    },
    "sync_upcoming_movies": {
        "task": "apps.movies.tasks.sync_upcoming_movies",
        "schedule": timedelta(days=7),
        "options": {"queue": "movies"},
    },
}

# Task routing
app.conf.task_routes = {
    "apps.movies.tasks.sync_*": {"queue": "movies"},
    "apps.movies.tasks.process_movie_data": {"queue": "movie_details"},
}
```

### Environment Variables

```bash
# IMDB API Configuration
IMDB_API_KEY=your_rapidapi_key
IMDB_API_HOST=imdb-api1.p.rapidapi.com
IMDB_API_DELAY=2  # seconds between calls

# Database
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Redis Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TIMEOUT=300  # 5 minutes for API responses

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## 🚨 MONITORING & TROUBLESHOOTING

### Key Metrics

```python
# Success Metrics
TASK_SUCCESS_RATE = successful_tasks / total_tasks * 100
MOVIES_WITH_COMPLETE_DATA = movies_score_8_9 / total_movies * 100
CACHE_HIT_RATE = cache_hits / total_requests * 100

# Performance Metrics
IMDB_API_RESPONSE_TIME = average_response_time_ms
DATABASE_QUERY_TIME = average_query_time_ms
SYNC_DURATION = sync_end_time - sync_start_time
```

### Common Issues

#### 1. Task Not Running

```bash
# Check status
celery -A config inspect scheduled
celery -A config inspect active

# Restart services
sudo systemctl restart celery-beat
sudo systemctl restart celery-worker
```

#### 2. IMDB API Rate Limits

```python
# Symptoms: 429 errors in logs
# Solution: Increase IMDB_API_DELAY from 2 to 5 seconds
# Or reduce batch size from 50 to 25 movies per sync
```

#### 3. Cache Performance Issues

```bash
# Check Redis memory
redis-cli info memory

# Clear stale cache
redis-cli eval "return redis.call('del', unpack(redis.call('keys', 'movie:*')))" 0
```

---

## 🎯 SUMMARY - ĐIỂM QUAN TRỌNG

### 🔄 Flow Tóm Tắt

1. **Celery Beat** trigger 3 tasks mỗi 7 ngày
2. **API Calls** lấy 50 movie IDs từ IMDB cho mỗi category
3. **Quick Flag Setting** đánh dấu is_popular/is_top_rated/is_upcoming
4. **Async Detail Processing** enrich thông tin chi tiết (poster, overview, ratings)
5. **Cache Management** update Redis cache cho performance
6. **API Serving** Django serve data cho React frontend với scoring algorithm

### 🎯 Tabs Logic

- **Trending:** `is_popular=True` + có poster + score theo data completeness
- **Top Rated:** `is_top_rated=True` + có poster + rating ≥ 7.0
- **Upcoming:** `is_upcoming=True` + có poster + release_date ≥ today

### ⚡ Performance Features

- **Parallel processing** cho 3 sync tasks
- **Multi-level caching** (individual movie + list + API response)
- **Data completeness scoring** ưu tiên movies đầy đủ thông tin
- **Rate limiting** tránh API limits
- **Async detail processing** không block main sync flow

---

**📝 Document Info:**

- **Created:** 2024-01-XX
- **Version:** 1.0
- **Authors:** Development Team
- **Purpose:** Complete system documentation for movie sync functionality
