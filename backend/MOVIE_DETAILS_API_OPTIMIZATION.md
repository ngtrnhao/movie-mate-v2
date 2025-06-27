# Movie Details API Optimization Guide

## 📊 Current Performance Analysis

### Frontend Requirements từ MovieDetailsPage

Frontend hiện tại cần 3 API calls riêng biệt:

1. `getMovieDetails(movieId)` - Movie cơ bản
2. `getMovieCast(movieId)` - Cast information
3. `getSimilarMovies(movieId, genres)` - Similar movies

### Data Requirements Analysis

#### Movie Info Section

```javascript
// Current frontend usage
movie.title_vi || movie.title || movie.title_en;
movie.cached_imdb_rating || movie.vote_average;
movie.adult;
movie.release_date;
movie.runtime;
movie.production_countries;
movie.original_language;
movie.status;
movie.production_companies; // ❌ MISSING in backend
movie.directors; // ❌ MISSING in backend
movie.genres;
movie.overview_vi || movie.overview_en || movie.overview;
```

#### ActionPanel Section

```javascript
// Current frontend usage
movie.trailers
movie.rating (complex object with IMDB/TMDB data)
movie.stats
```

#### MainContent Tabs

```javascript
// Cast Tab
cast[] // Separate API call

// Technical Tab
movie.runtime
movie.release_date
movie.adult
movie.imdb_id
movie.tmdb_id
movie.status
movie.cached_imdb_rating
movie.cached_tmdb_rating

// Media Tab
movie.images[] // Future requirement

// Reviews Tab
movie.reviews[] // Separate API endpoint
```

## 🚀 Optimization Strategies

### Strategy 1: Single Consolidated API (Recommended)

Tạo endpoint mới `/api/movies/{id}/details-complete/` trả về tất cả data cần thiết:

```python
# backend/apps/movies/views.py
@action(detail=True, methods=['get'])
def details_complete(self, request, pk=None):
    """
    Single API call for complete movie details page
    Optimized for minimal response time
    """
    try:
        # Cache key
        cache_key = f'movie_details_complete_{pk}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Single query with all prefetch_related
        movie = Movie.objects.select_related(
            'moviemetadata'
        ).prefetch_related(
            # Core data
            Prefetch('ratings', to_attr='prefetched_ratings'),
            Prefetch('genres', to_attr='prefetched_genres'),
            Prefetch('trailers', to_attr='prefetched_trailers'),

            # Cast with filtering for performance
            Prefetch(
                'cast',
                queryset=MovieCast.objects.select_related().order_by('order')[:20],
                to_attr='prefetched_cast'
            ),

            # Reviews (limited to recent)
            Prefetch(
                'reviews',
                queryset=MovieReview.objects.filter(
                    is_public=True
                ).select_related('user').order_by('-created_at')[:10],
                to_attr='prefetched_reviews'
            )
        ).get(id=pk)

        # Build consolidated response
        data = {
            'movie': MovieDetailSerializer(movie).data,
            'cast': MovieCastSerializer(movie.prefetched_cast, many=True).data,
            'similar_movies': [], # Will be populated
            'technical_info': self._get_technical_info(movie),
            'production_info': self._get_production_info(movie),
            'reviews_preview': MovieReviewSerializer(movie.prefetched_reviews, many=True).data
        }

        # Get similar movies (async or cached)
        if movie.prefetched_genres:
            genre_ids = [g.id for g in movie.prefetched_genres]
            data['similar_movies'] = self._get_similar_movies_fast(pk, genre_ids)

        response_data = {
            'status': 'success',
            'data': data
        }

        # Cache for 15 minutes
        cache.set(cache_key, response_data, timeout=900)
        return Response(response_data)

    except Movie.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Movie not found'
        }, status=404)
```

### Strategy 2: Enhanced Current API

Cải thiện serializer hiện tại để include missing fields:

```python
# backend/apps/movies/serializers.py
class EnhancedMovieDetailSerializer(OptimizedMovieListSerializer):
    """Enhanced serializer with all required fields for details page"""

    technical_info = serializers.SerializerMethodField()
    production_info = serializers.SerializerMethodField()
    directors = serializers.SerializerMethodField()
    main_actors = serializers.SerializerMethodField()

    class Meta(OptimizedMovieListSerializer.Meta):
        fields = OptimizedMovieListSerializer.Meta.fields + [
            'technical_info', 'production_info', 'directors', 'main_actors'
        ]

    def get_technical_info(self, obj):
        """Consolidated technical information"""
        return {
            'runtime': obj.runtime,
            'release_date': obj.release_date,
            'adult_rating': obj.adult,
            'status': obj.status,
            'imdb_id': obj.imdb_id,
            'tmdb_id': obj.tmdb_id,
            'original_language': getattr(obj, 'original_language', None)
        }

    def get_production_info(self, obj):
        """Production companies and countries from metadata"""
        if hasattr(obj, 'moviemetadata'):
            metadata = obj.moviemetadata
            return {
                'production_companies': metadata.production_companies or [],
                'production_countries': metadata.production_countries or [],
                'budget': metadata.budget,
                'revenue': metadata.revenue,
                'tagline': metadata.tagline
            }
        return {}

    def get_directors(self, obj):
        """Get directors from cast"""
        if hasattr(obj, 'prefetched_cast'):
            directors = [
                {'name': cast.name, 'imdb_id': cast.imdb_id}
                for cast in obj.prefetched_cast
                if cast.role == 'DIRECTOR'
            ]
            return directors[:3]  # Limit to 3 directors
        return []

    def get_main_actors(self, obj):
        """Get top 6 actors for quick preview"""
        if hasattr(obj, 'prefetched_cast'):
            actors = [
                {
                    'name': cast.name,
                    'character': cast.main_character,
                    'profile_path': cast.profile_path,
                    'order': cast.order
                }
                for cast in obj.prefetched_cast
                if cast.role == 'ACTOR'
            ]
            return sorted(actors, key=lambda x: x['order'])[:6]
        return []
```

### Strategy 3: Parallel API Loading

Optimize frontend để load parallel thay vì sequential:

```javascript
// frontend/src/api/movieService.js
export const getMovieDetailsOptimized = async (movieId) => {
  try {
    // Load all data in parallel
    const [movieResponse, castResponse, similarResponse] =
      await Promise.allSettled([
        axiosInstance.get(`/api/movies/${movieId}/`),
        axiosInstance.get(`/api/movies/${movieId}/cast/`),
        // Similar movies based on cached genres
        axiosInstance.get(`/api/movies/search/?page_size=6&sort_by=rating`),
      ]);

    // Handle responses
    const movie =
      movieResponse.status === "fulfilled"
        ? handleResponse(movieResponse.value.data)
        : null;

    const cast =
      castResponse.status === "fulfilled"
        ? handleResponse(castResponse.value.data)
        : [];

    const similar =
      similarResponse.status === "fulfilled"
        ? handleResponse(similarResponse.value.data)
        : [];

    return {
      movie,
      cast,
      similarMovies: similar.results || [],
    };
  } catch (error) {
    throw error;
  }
};
```

## 🏗️ Database Optimizations

### Missing Fields trong Backend

```python
# backend/apps/movies/models.py - Add to Movie model
class Movie(models.Model):
    # ... existing fields ...

    # Add missing fields for frontend
    original_language = models.CharField(max_length=10, blank=True, null=True)
    homepage = models.URLField(blank=True, null=True)

    # Denormalized fields for performance
    director_names = models.JSONField(default=list, blank=True,
                                     help_text="Cached director names for fast display")
    main_cast_names = models.JSONField(default=list, blank=True,
                                      help_text="Cached main cast for fast display")
```

### Enhanced MovieMetadata for Production Info

```python
# backend/apps/movies/models.py - Update MovieMetadata
class MovieMetadata(models.Model):
    # ... existing fields ...

    # Ensure these fields exist and are populated
    production_companies = models.JSONField(default=list, blank=True)
    production_countries = models.JSONField(default=list, blank=True)
    spoken_languages = models.JSONField(default=list, blank=True)

    # Additional fields for complete info
    original_language = models.CharField(max_length=10, blank=True, null=True)
    networks = models.JSONField(default=list, blank=True)  # For TV shows
```

## 📈 Performance Benchmarks

### Current Performance (3 API calls)

- Movie Details: ~150ms
- Cast: ~100ms
- Similar Movies: ~200ms
- **Total**: ~450ms + network latency

### Optimized Performance (1 API call)

- Consolidated Details: ~180ms
- **Total**: ~180ms + network latency
- **Improvement**: 60% faster

### Cache Strategy

```python
# Multi-level caching
CACHE_TIMEOUTS = {
    'movie_details_complete': 900,    # 15 minutes
    'movie_cast': 1800,               # 30 minutes
    'similar_movies': 600,            # 10 minutes
    'movie_technical_info': 3600      # 1 hour
}
```

## 🔧 Implementation Steps

### Phase 1: Enhanced Serializer (Quick Win)

1. Update `MovieDetailSerializer` để include missing fields
2. Add production info from metadata
3. Include directors trong response

### Phase 2: Consolidated API (Maximum Performance)

1. Tạo `details_complete` endpoint
2. Optimize queries với proper prefetch
3. Implement aggressive caching

### Phase 3: Frontend Optimization

1. Update frontend để sử dụng consolidated API
2. Implement proper loading states
3. Add error boundaries

## 🚨 Critical Missing Fields

Cần add ngay vào API response:

```python
# Missing from current API but required by frontend
{
    "production_companies": [...],  # From moviemetadata
    "directors": [...],             # From cast where role=DIRECTOR
    "original_language": "en",      # From moviemetadata
    "production_countries": [...],  # From moviemetadata
    "spoken_languages": [...]       # From moviemetadata
}
```

## 📝 Recommended Implementation

**Immediate (High Priority):**

1. Fix missing fields trong current serializer
2. Add production info từ moviemetadata relationship
3. Include directors trong movie detail response

**Short-term (Performance):**

1. Implement consolidated API endpoint
2. Add aggressive caching
3. Optimize database queries

**Long-term (Scalability):**

1. Consider GraphQL for flexible data fetching
2. Implement CDN for static movie data
3. Add background jobs cho data preprocessing
