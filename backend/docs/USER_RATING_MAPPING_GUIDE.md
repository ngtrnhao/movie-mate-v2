# 📊 Hướng dẫn Mapping Dữ liệu Rating với User Thực - Movie Recommendation System

## 🔍 Tổng quan hệ thống

Dự án Movie Recommendation System đã có cấu trúc rating hoàn chỉnh với:

### 📋 **Models chính:**

1. **`User`** - User management system
2. **`Movie`** - Movie database với cached rating fields
3. **`MovieRating`** - External ratings (IMDB, TMDB, etc.)
4. **`MovieReview`** - Unified user reviews và external reviews
5. **`UserFavoriteGenre`** - User preferences

### 🎯 **Cấu trúc Rating hiện tại:**

```python
# External ratings (IMDB, TMDB, Rotten Tomatoes)
MovieRating:
    - imdb_rating, imdb_votes
    - tmdb_rating, tmdb_votes
    - metacritic_rating
    - rotten_tomatoes_rating, rotten_tomatoes_votes

# User ratings (thông qua MovieReview)
MovieReview:
    - user (ForeignKey to User)
    - movie (ForeignKey to Movie)
    - rating (0.0 - 5.0 scale)
    - review_type ('USER' | 'EXTERNAL')
    - content, title
    - is_public, is_spoiler
```

## 🚀 Cách Import Dataset Rating

### **1. Sử dụng Management Command (Khuyên dùng)**

```bash
# Import MovieLens dataset
python manage.py import_user_rating_dataset \
    --dataset-path /path/to/ratings.csv \
    --format movielens \
    --create-users \
    --batch-size 1000 \
    --skip-existing

# Import với mapping user hiện có
python manage.py import_user_rating_dataset \
    --dataset-path /path/to/ratings.csv \
    --format movielens \
    --map-existing-users \
    --batch-size 1000

# Dry run để test
python manage.py import_user_rating_dataset \
    --dataset-path /path/to/ratings.csv \
    --format movielens \
    --create-users \
    --dry-run
```

### **2. Format Dataset được hỗ trợ:**

#### **MovieLens Format:**

```csv
userId,movieId,rating,timestamp
1,tt0114709,4.5,1260759144
2,tt0113277,3.0,1260759179
```

#### **IMDB Format:**

```csv
user_id,imdb_id,rating,review_text,review_date
user123,tt0114709,4.5,"Great movie!",2023-01-15
```

#### **Custom Format:**

```csv
user_identifier,movie_identifier,rating,review_title,review_content,timestamp
user_001,tt0114709,4.5,"Amazing","This movie is fantastic",1260759144
```

### **3. Sử dụng UserRatingService (Programmatic)**

```python
from apps.movies.services.user_rating_service import UserRatingService

# Create individual rating
user = User.objects.get(id=1)
movie = Movie.objects.get(imdb_id='tt0114709')
rating_service = UserRatingService()

review = rating_service.create_user_rating(
    user=user,
    movie=movie,
    rating=4.5,
    title="Great movie!",
    content="I really enjoyed this film",
    is_public=True
)

# Bulk import
ratings_data = [
    {'user': user1, 'movie': movie1, 'rating': 4.5, 'created_at': datetime.now()},
    {'user': user2, 'movie': movie2, 'rating': 3.0, 'created_at': datetime.now()},
]

result = rating_service.bulk_import_ratings(ratings_data, batch_size=1000)
print(f"Created: {result['total_created']}, Errors: {result['total_errors']}")
```

## 🔧 Strategies Mapping User

### **Strategy 1: Tạo Synthetic Users**

```python
# Tạo users mới dựa trên dataset
--create-users
```

- **Ưu điểm:** Giữ nguyên user ID từ dataset, dễ trace
- **Nhược điểm:** Tạo ra users giả, không phải real users

### **Strategy 2: Map với Existing Users**

```python
# Map ratings với users hiện có trong system
--map-existing-users
```

- **Ưu điểm:** Sử dụng real users, realistic data
- **Nhược điểm:** Mất mapping gốc với dataset

### **Strategy 3: Hybrid Approach**

```python
# 1. Import một phần dataset với existing users
python manage.py import_user_rating_dataset \
    --dataset-path /path/to/ratings_sample.csv \
    --map-existing-users \
    --batch-size 500

# 2. Tạo synthetic users cho phần còn lại
python manage.py import_user_rating_dataset \
    --dataset-path /path/to/ratings_remaining.csv \
    --create-users \
    --batch-size 500
```

## 📈 Analytics và Recommendations

### **1. User Rating Statistics**

```python
from apps.movies.services.user_rating_service import UserRatingService

# Get user stats
user = User.objects.get(id=1)
stats = UserRatingService.calculate_user_rating_stats(user)

print(f"Total ratings: {stats['total_ratings']}")
print(f"Average rating: {stats['average_rating']}")
print(f"Favorite genres: {stats['favorite_genres']}")
```

### **2. Movie Rating Statistics**

```python
# Get movie stats
movie = Movie.objects.get(imdb_id='tt0114709')
stats = UserRatingService.calculate_movie_rating_stats(movie)

print(f"Total user ratings: {stats['total_user_ratings']}")
print(f"Average user rating: {stats['average_user_rating']}")
```

### **3. Collaborative Filtering Recommendations**

```python
# Get recommendations for user
user = User.objects.get(id=1)
recommendations = UserRatingService.get_user_recommendations_based_on_ratings(user, limit=20)

for movie in recommendations:
    print(f"Recommended: {movie.title} ({movie.cached_imdb_rating})")
```

### **4. Trending Movies**

```python
# Get trending movies based on user ratings
trending = UserRatingService.get_trending_movies_by_user_ratings(days=7, limit=20)

for movie in trending:
    print(f"Trending: {movie.title}")
```

## 🛠️ Performance Optimization

### **1. Database Indexes**

Hệ thống đã có indexes tối ưu:

```python
# MovieReview indexes
models.Index(fields=["user", "movie"])
models.Index(fields=["movie", "rating"])
models.Index(fields=["review_type", "created_at"])

# Movie cached rating indexes
models.Index(fields=["cached_imdb_rating"])
models.Index(fields=["combined_rating_score"])
```

### **2. Caching Strategy**

```python
# Cache user ratings
cache_key = f"user_ratings_{user.id}"
user_ratings = cache.get(cache_key)
if not user_ratings:
    user_ratings = UserRatingService.get_user_ratings(user, limit=100)
    cache.set(cache_key, user_ratings, timeout=3600)

# Cache movie stats
cache_key = f"movie_stats_{movie.id}"
movie_stats = cache.get(cache_key)
if not movie_stats:
    movie_stats = UserRatingService.calculate_movie_rating_stats(movie)
    cache.set(cache_key, movie_stats, timeout=1800)
```

### **3. Batch Processing**

```python
# Process large datasets in batches
for i in range(0, len(ratings_data), 1000):
    batch = ratings_data[i:i+1000]
    UserRatingService.bulk_import_ratings(batch, batch_size=1000)
    time.sleep(1)  # Prevent overwhelming the database
```

## 🔄 API Endpoints

### **1. Create User Rating**

```python
POST /api/movies/{movie_id}/reviews/
{
    "rating": 4.5,
    "title": "Great movie!",
    "content": "I really enjoyed this film",
    "is_public": true,
    "is_spoiler": false
}
```

### **2. Get User Ratings**

```python
GET /api/users/{user_id}/ratings/
# Returns paginated list of user ratings
```

### **3. Get Movie Reviews**

```python
GET /api/movies/{movie_id}/reviews/?type=USER
# Returns user reviews for the movie
```

## 📊 Sample Import Scripts

### **Script 1: Import MovieLens Small Dataset**

```bash
#!/bin/bash

# Download MovieLens dataset
wget http://files.grouplens.org/datasets/movielens/ml-latest-small.zip
unzip ml-latest-small.zip

# Import ratings
python manage.py import_user_rating_dataset \
    --dataset-path ml-latest-small/ratings.csv \
    --format movielens \
    --create-users \
    --batch-size 1000 \
    --skip-existing

echo "Import completed!"
```

### **Script 2: Generate Sample Rating Data**

```python
# scripts/generate_sample_ratings.py
import csv
import random
from datetime import datetime, timedelta

def generate_sample_ratings(output_file, num_users=1000, num_movies=100, num_ratings=10000):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['userId', 'movieId', 'rating', 'timestamp'])

        for i in range(num_ratings):
            user_id = random.randint(1, num_users)
            movie_id = f"tt{random.randint(1000000, 9999999):07d}"
            rating = random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])
            timestamp = int((datetime.now() - timedelta(days=random.randint(1, 365))).timestamp())

            writer.writerow([user_id, movie_id, rating, timestamp])

if __name__ == "__main__":
    generate_sample_ratings('sample_ratings.csv')
    print("Sample ratings generated!")
```

## ⚠️ Lưu ý quan trọng

### **1. Data Consistency**

- Đảm bảo movie IDs trong dataset match với movies trong database
- Validate rating values (0.0-5.0 scale)
- Handle missing or invalid data gracefully

### **2. Performance Considerations**

- Import large datasets trong non-peak hours
- Sử dụng batch processing để tránh overwhelming database
- Monitor memory usage khi process large files

### **3. User Privacy**

- Set appropriate `is_public` flags
- Consider data anonymization for imported ratings
- Comply với privacy regulations

### **4. Backup Strategy**

```bash
# Backup before import
python manage.py dumpdata movies.MovieReview > backup_reviews.json

# Restore if needed
python manage.py loaddata backup_reviews.json
```

## 🎯 Next Steps

1. **Import your dataset** sử dụng management command
2. **Verify data integrity** với dry-run trước
3. **Optimize recommendations** bằng cách tune collaborative filtering parameters
4. **Monitor performance** và adjust batch sizes nếu cần
5. **Implement caching** cho frequently accessed data

---

📝 **Documentation này sẽ được update khi có thêm features mới hoặc optimization improvements.**

# User Rating API & Service Guide

## 🔧 API Usage

### **Rating Creation API:**

```python
# Create single rating
from apps.movies.services.user_rating_service import UserRatingService

# Via API endpoint
POST /api/movies/{movie_id}/rate/
{
    "rating": 4.5,
    "comment": "Great movie!"
}

# Via service directly
rating = UserRatingService.create_rating(
    user=user,
    movie=movie,
    rating=4.5,
    comment="Great movie!"
)
```

### **Bulk Rating Operations:**

```python
# Bulk create ratings
ratings_data = [
    {'user_id': 1, 'movie_id': 100, 'rating': 4.5},
    {'user_id': 1, 'movie_id': 101, 'rating': 3.0},
]

created_ratings = UserRatingService.bulk_create_ratings(ratings_data)

# Update existing ratings
UserRatingService.update_rating(rating_id=123, rating=5.0, comment="Updated!")

# Delete rating
UserRatingService.delete_rating(rating_id=123)
```

### **Recommendation API:**

```python
# Get user-based recommendations
GET /api/users/{user_id}/recommendations/

# Get collaborative filtering recommendations
recommendations = UserRatingService.get_collaborative_recommendations(
    user_id=user.id,
    limit=10
)

# Get user similarity
similar_users = UserRatingService.get_similar_users(user_id=user.id, limit=5)
```

---

## 🗄️ Database Schema

### **Models Overview:**

```python
# User ratings stored as MovieReview
class MovieReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=2)  # 0.0-5.0
    comment = models.TextField(blank=True)
    review_type = models.CharField(default='USER')  # USER, CRITIC, IMDB
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'movie', 'review_type']

# External ratings (IMDB, TMDB) stored as MovieRating
class MovieRating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    source = models.CharField(max_length=20)  # IMDB, TMDB, ROTTEN_TOMATOES
    rating = models.DecimalField(max_digits=4, decimal_places=2)
    vote_count = models.IntegerField(default=0)
    max_rating = models.DecimalField(max_digits=4, decimal_places=2, default=10.0)
```

### **Key Indexes:**

```sql
-- For fast user rating lookups
CREATE INDEX idx_moviereview_user_movie ON movies_moviereview(user_id, movie_id);

-- For collaborative filtering
CREATE INDEX idx_moviereview_user_rating ON movies_moviereview(user_id, rating);
CREATE INDEX idx_moviereview_movie_rating ON movies_moviereview(movie_id, rating);

-- For recommendation queries
CREATE INDEX idx_moviereview_rating_created ON movies_moviereview(rating, created_at);
```

---

## ⚙️ Service Configuration

### **UserRatingService Settings:**

```python
# In settings.py
RATING_SETTINGS = {
    'MIN_RATING': 0.0,
    'MAX_RATING': 5.0,
    'RATING_PRECISION': 2,  # decimal places
    'COLLABORATIVE_FILTERING': {
        'MIN_COMMON_MOVIES': 5,
        'MIN_SIMILAR_USERS': 10,
        'SIMILARITY_THRESHOLD': 0.1,
    },
    'CACHE_TIMEOUT': 3600,  # 1 hour
    'BATCH_SIZE': 1000,
}
```

### **Cache Keys:**

```python
# User ratings cache
f"user_ratings:{user_id}"
f"user_avg_rating:{user_id}"
f"movie_user_ratings:{movie_id}"

# Collaborative filtering cache
f"similar_users:{user_id}"
f"user_recommendations:{user_id}"
f"movie_similarity:{movie_id}"
```

---

## 🧮 Collaborative Filtering Algorithm

### **User Similarity Calculation:**

```python
def calculate_user_similarity(user1_ratings, user2_ratings):
    """
    Pearson correlation coefficient between two users
    """
    common_movies = set(user1_ratings.keys()) & set(user2_ratings.keys())

    if len(common_movies) < MIN_COMMON_MOVIES:
        return 0

    # Calculate means
    mean1 = sum(user1_ratings[m] for m in common_movies) / len(common_movies)
    mean2 = sum(user2_ratings[m] for m in common_movies) / len(common_movies)

    # Calculate Pearson correlation
    numerator = sum((user1_ratings[m] - mean1) * (user2_ratings[m] - mean2)
                   for m in common_movies)

    sum1_sq = sum((user1_ratings[m] - mean1) ** 2 for m in common_movies)
    sum2_sq = sum((user2_ratings[m] - mean2) ** 2 for m in common_movies)

    denominator = (sum1_sq * sum2_sq) ** 0.5

    return numerator / denominator if denominator != 0 else 0
```

### **Recommendation Generation:**

```python
def generate_recommendations(user_id, limit=10):
    """
    Generate movie recommendations using collaborative filtering
    """
    # Get user's ratings
    user_ratings = get_user_ratings(user_id)

    # Find similar users
    similar_users = get_similar_users(user_id, limit=50)

    # Aggregate ratings from similar users
    recommendations = defaultdict(list)

    for similar_user, similarity in similar_users:
        similar_user_ratings = get_user_ratings(similar_user.id)

        for movie_id, rating in similar_user_ratings.items():
            if movie_id not in user_ratings:  # User hasn't rated this movie
                recommendations[movie_id].append(rating * similarity)

    # Calculate weighted average and sort
    final_recommendations = []
    for movie_id, weighted_ratings in recommendations.items():
        avg_rating = sum(weighted_ratings) / len(weighted_ratings)
        final_recommendations.append((movie_id, avg_rating))

    # Sort by predicted rating and return top N
    final_recommendations.sort(key=lambda x: x[1], reverse=True)
    return final_recommendations[:limit]
```

---

## 🔍 Query Optimization

### **Efficient Rating Queries:**

```python
# Get user ratings with movie details
user_ratings = MovieReview.objects.filter(
    user=user,
    review_type='USER'
).select_related('movie').prefetch_related('movie__genres')

# Get movie ratings with user details
movie_ratings = MovieReview.objects.filter(
    movie=movie,
    review_type='USER'
).select_related('user').order_by('-rating', '-created_at')

# Aggregate queries for statistics
from django.db.models import Avg, Count, Max, Min

movie_stats = MovieReview.objects.filter(
    movie=movie,
    review_type='USER'
).aggregate(
    avg_rating=Avg('rating'),
    total_ratings=Count('rating'),
    max_rating=Max('rating'),
    min_rating=Min('rating')
)
```

### **Bulk Operations:**

```python
# Bulk create ratings (efficient for large imports)
from django.db import transaction

def bulk_import_ratings(ratings_data, batch_size=1000):
    with transaction.atomic():
        for i in range(0, len(ratings_data), batch_size):
            batch = ratings_data[i:i + batch_size]

            rating_objects = [
                MovieReview(
                    user_id=data['user_id'],
                    movie_id=data['movie_id'],
                    rating=data['rating'],
                    comment=data.get('comment', ''),
                    review_type='USER'
                ) for data in batch
            ]

            MovieReview.objects.bulk_create(
                rating_objects,
                ignore_conflicts=True  # Skip duplicates
            )
```

---

## 📊 Performance Monitoring

### **Key Metrics to Track:**

```python
# Rating system metrics
total_ratings = MovieReview.objects.filter(review_type='USER').count()
active_users = MovieReview.objects.filter(review_type='USER').values('user').distinct().count()
avg_ratings_per_user = total_ratings / active_users if active_users > 0 else 0

# Recommendation performance
recommendation_cache_hit_rate = cache.get('recommendation_cache_hits', 0) / cache.get('recommendation_requests', 1)
avg_recommendation_generation_time = cache.get('avg_recommendation_time', 0)

# Database performance
slow_queries = get_slow_query_log()  # Custom function to check DB logs
connection_pool_usage = get_db_connection_stats()
```

### **Monitoring Queries:**

```sql
-- Find slow rating queries
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE query LIKE '%moviereview%'
ORDER BY mean_time DESC LIMIT 10;

-- Check rating distribution
SELECT rating, COUNT(*) as count
FROM movies_moviereview
WHERE review_type = 'USER'
GROUP BY rating
ORDER BY rating;

-- Most active users
SELECT user_id, COUNT(*) as rating_count
FROM movies_moviereview
WHERE review_type = 'USER'
GROUP BY user_id
ORDER BY rating_count DESC
LIMIT 20;
```

---

## 🚀 Production Deployment

### **Environment Variables:**

```bash
# Rating system configuration
RATING_MIN_VALUE=0.0
RATING_MAX_VALUE=5.0
RATING_CACHE_TIMEOUT=3600
COLLABORATIVE_MIN_USERS=10
RECOMMENDATION_CACHE_SIZE=1000

# Database optimization
DB_RATING_BATCH_SIZE=1000
DB_CONNECTION_POOL_SIZE=20
DB_RATING_INDEX_MAINTENANCE=true
```

### **Monitoring & Alerts:**

```python
# Custom monitoring for rating system
class RatingSystemMonitor:
    def check_system_health(self):
        return {
            'total_ratings': self.get_total_ratings(),
            'rating_growth_rate': self.get_daily_growth(),
            'avg_response_time': self.get_avg_response_time(),
            'error_rate': self.get_error_rate(),
            'cache_hit_rate': self.get_cache_hit_rate()
        }

    def alert_if_needed(self, metrics):
        if metrics['error_rate'] > 0.05:  # > 5% error rate
            send_alert("High error rate in rating system")

        if metrics['avg_response_time'] > 500:  # > 500ms
            send_alert("Slow rating system response")
```

---

## 📝 Summary

**UserRatingService** provides complete functionality for:

✅ **CRUD Operations**: Create, read, update, delete ratings
✅ **Bulk Operations**: Efficient import/export của large datasets
✅ **Collaborative Filtering**: User similarity & recommendations
✅ **Performance**: Optimized queries với caching
✅ **Monitoring**: Health checks & performance metrics
✅ **Production Ready**: Scalable architecture với proper indexing

**Ready for production use với real user rating data!**
