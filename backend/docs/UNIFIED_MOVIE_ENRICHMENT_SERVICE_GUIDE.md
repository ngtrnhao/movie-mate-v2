# 🎬 Unified Movie Enrichment Service - Complete Guide

## Overview

The **Unified Movie Enrichment Service** is a comprehensive solution that consolidates all movie data fetching and enrichment services (TMDB, IMDB) into a single, powerful service designed specifically for admin dashboard use.

## 🎯 Key Features

### ✨ Core Capabilities

- **🔄 TMDB ID Mapping**: Automatically map TMDB IDs from IMDB IDs for movies imported from datasets
- **🌍 Multilingual Support**: Enrich titles and overviews in both English and Vietnamese
- **🖼️ Visual Assets**: Comprehensive poster, backdrop, and image enrichment
- **🎭 Rich Metadata**: Cast, crew, genres, trailers, keywords, and production information
- **⭐ Multi-source Ratings**: TMDB, IMDB, and other rating platforms
- **🎯 Quality-driven**: Automatically resolve quality issues and suggestions
- **⚡ Performance Optimized**: Batch processing with rate limiting and intelligent caching

### 🧠 Smart Features

- **Quality-based Enrichment**: Target specific quality issues for efficient processing
- **Intelligent Planning**: Auto-detect what needs enrichment based on current data state
- **Rate Limiting**: Built-in API rate limiting to respect external service limits
- **Error Handling**: Comprehensive error handling with detailed logging
- **Progress Tracking**: Real-time progress and quality improvement tracking

## 🏗️ Architecture

### Service Structure

```
UnifiedMovieEnrichmentService
├── Core Enrichment Methods
│   ├── enrich_movie_comprehensive()
│   ├── enrich_movie_by_quality_issues()
│   └── batch_enrich_movies()
├── TMDB ID Mapping
│   └── _ensure_tmdb_id_mapping()
├── Data Category Methods
│   ├── _enrich_basic_information()
│   ├── _enrich_visual_assets()
│   ├── _enrich_metadata_richness()
│   └── _enrich_rating_information()
├── Analysis & Planning
│   ├── _create_enrichment_plan()
│   ├── _get_current_quality_metrics()
│   └── _map_quality_issues_to_focus_areas()
└── Utility Methods
    ├── get_enrichment_status()
    └── validate_enrichment_requirements()
```

### Integration Services

- **TMDBService**: Primary data source (free API)
- **IMDBService**: Secondary source and ID mapping
- **MovieTitleGenreService**: Multilingual title and genre handling
- **MovieOverviewService**: Multilingual overview enrichment
- **QualityCalculationService**: Quality assessment and scoring

## 🚀 Usage Guide

### 1. Individual Movie Enrichment

#### Comprehensive Enrichment

```python
from apps.movies.services.unified_movie_enrichment_service import UnifiedMovieEnrichmentService

service = UnifiedMovieEnrichmentService()

# Comprehensive enrichment (all data)
result = service.enrich_movie_comprehensive(
    movie=movie_instance,
    force_refresh=False,
    focus_areas=None  # None = all areas
)
```

#### Quality-based Enrichment

```python
# Target specific quality issues
result = service.enrich_movie_by_quality_issues(movie_instance)
```

#### Focused Enrichment

```python
# Focus on specific areas
result = service.enrich_movie_comprehensive(
    movie=movie_instance,
    focus_areas=['basic', 'visual']  # basic, visual, metadata, ratings
)
```

### 2. Batch Processing

```python
# Batch enrich multiple movies
movie_ids = [1, 2, 3, 4, 5]
result = service.batch_enrich_movies(
    movie_ids=movie_ids,
    focus_areas=['basic', 'visual'],
    max_concurrent=5
)
```

### 3. Status and Analysis

```python
# Get enrichment status
status = service.get_enrichment_status(movie_instance)

# Validate requirements
validation = service.validate_enrichment_requirements(movie_instance)
```

## 📡 API Endpoints

### Admin Endpoints

#### 1. Enrich Single Movie

```http
POST /api/movies/admin/movies/{movie_id}/enrich/
```

**Request Body:**

```json
{
  "force_refresh": false,
  "focus_areas": ["basic", "visual", "metadata", "ratings"],
  "enrich_type": "comprehensive"
}
```

**Response:**

```json
{
  "success": true,
  "movie_id": 123,
  "movie_title": "Example Movie",
  "enrichment_result": {
    "success": true,
    "quality_before": {"quality_score": 6.5},
    "quality_after": {"quality_score": 8.2},
    "improvements": ["Quality score: 6.5 → 8.2"],
    "operations": {...},
    "processing_time": 3.45
  }
}
```

#### 2. Batch Enrichment

```http
POST /api/movies/admin/movies/batch-enrich/
```

**Request Body:**

```json
{
  "movie_ids": [1, 2, 3, 4, 5],
  "focus_areas": ["basic", "visual"],
  "max_concurrent": 5
}
```

#### 3. Enrichment Status

```http
GET /api/movies/admin/movies/{movie_id}/enrichment-status/
```

#### 4. Quality-based Enrichment

```http
POST /api/movies/admin/movies/enrich-quality-issues/
```

**Request Body:**

```json
{
  "quality_score_max": 7.0,
  "has_quality_issues": true,
  "limit": 50
}
```

## 🎛️ Frontend Integration

### Admin Component Usage

```jsx
import {
  enrichMovie,
  batchEnrichMovies,
  getMovieEnrichmentStatus,
} from "../../../api/adminMovieService";

// Enrich single movie
const result = await enrichMovie(movieId, {
  forceRefresh: false,
  focusAreas: ["basic", "visual"],
  enrichType: "comprehensive",
});

// Batch enrichment
const batchResult = await batchEnrichMovies([1, 2, 3], {
  focusAreas: ["metadata"],
  maxConcurrent: 3,
});

// Get status
const status = await getMovieEnrichmentStatus(movieId);
```

### Movie Enrichment Panel

The `MovieEnrichmentPanel` component provides a complete admin interface for:

- Individual movie enrichment
- Batch processing
- Quality-based enrichment
- Real-time status monitoring
- Configuration options

## 🧪 Testing & Validation

### Management Command Testing

```bash
# Test single movie
python manage.py test_unified_enrichment --movie-id=123 --show-status

# Test sample movies
python manage.py test_unified_enrichment --sample-size=10 --enrich-type=quality_based

# Test specific focus areas
python manage.py test_unified_enrichment --focus-areas basic visual --force-refresh
```

### Performance Testing

```bash
# Test with comprehensive enrichment
python manage.py test_unified_enrichment --sample-size=20 --enrich-type=comprehensive

# Test quality-based enrichment
python manage.py test_unified_enrichment --sample-size=50 --enrich-type=quality_based
```

## ⚙️ Configuration

### Rate Limiting Settings

```python
class UnifiedMovieEnrichmentService:
    def __init__(self):
        # Rate limiting for external APIs
        self.rate_limit_delay = 0.5  # 500ms between requests
        self.batch_delay = 2.0       # 2s between batches
```

### Focus Areas

| Focus Area | Description             | Includes                                                 |
| ---------- | ----------------------- | -------------------------------------------------------- |
| `basic`    | Basic movie information | Titles (EN/VI), Overviews (EN/VI), Release date, Runtime |
| `visual`   | Visual assets           | Poster URLs, Backdrop URLs, Additional images            |
| `metadata` | Rich metadata           | Cast, Genres, Trailers, Keywords, Production info        |
| `ratings`  | Rating information      | TMDB ratings, IMDB ratings, Cached ratings               |

### Enrichment Types

| Type            | Description                    | Use Case                          |
| --------------- | ------------------------------ | --------------------------------- |
| `comprehensive` | Enrich all available data      | New movies, major updates         |
| `quality_based` | Target specific quality issues | Maintenance, quality improvements |

## 📊 Quality Metrics Integration

### Quality-based Enrichment Strategy

The service automatically analyzes quality issues and maps them to focus areas:

```python
quality_issues = [
    "Missing English overview",
    "No poster image",
    "Missing cast information"
]

# Automatically mapped to:
focus_areas = ['basic', 'visual', 'metadata']
```

### Quality Improvements Tracking

```python
improvements = [
    "Quality score: 6.5 → 8.2",
    "Completeness: 65% → 85%",
    "Issues resolved: 3",
    "Minimum quality threshold now met"
]
```

## 🔧 Maintenance & Operations

### Database Optimization

```bash
# Run quality calculation for movies
python manage.py calculate_quality_scores --batch-size=100

# Index movies in Elasticsearch
python manage.py index_movies --with-quality-metrics

# Test calculation pipeline
python manage.py test_calculation_pipeline --sample-size=10
```

### Performance Monitoring

```bash
# Monitor search performance
python manage.py test_elasticsearch --quality-metrics

# Test enrichment performance
python manage.py test_unified_enrichment --sample-size=100
```

## 🚨 Error Handling & Troubleshooting

### Common Issues

#### 1. TMDB API Rate Limiting

```python
# Built-in rate limiting handles this automatically
# Adjust delays if needed:
service.rate_limit_delay = 1.0  # Increase delay
```

#### 2. Missing TMDB ID

```python
# Service automatically attempts mapping
# Manual mapping:
tmdb_id = service._ensure_tmdb_id_mapping(movie)
```

#### 3. Quality Calculation Errors

```python
# Check quality service status
validation = service.validate_enrichment_requirements(movie)
```

### Logging

```python
import logging
logger = logging.getLogger('apps.movies.services.unified_movie_enrichment_service')

# Enable debug logging
logger.setLevel(logging.DEBUG)
```

## 📈 Performance Metrics

### Expected Performance

| Operation                    | Average Time  | Success Rate |
| ---------------------------- | ------------- | ------------ |
| Single Movie (Comprehensive) | 3-5 seconds   | 95%+         |
| Single Movie (Quality-based) | 1-3 seconds   | 98%+         |
| Batch (10 movies)            | 30-60 seconds | 90%+         |
| TMDB ID Mapping              | 0.5-1 second  | 85%+         |

### Optimization Tips

1. **Use Quality-based Enrichment** for maintenance tasks
2. **Batch Processing** for multiple movies
3. **Focus Areas** to limit scope when possible
4. **Rate Limiting** respect API limits
5. **Caching** leverages built-in caching mechanisms

## 🔮 Future Enhancements

### Planned Features

- **🤖 AI-powered Quality Assessment**: Machine learning for quality prediction
- **🔄 Automatic Scheduling**: Background enrichment scheduling
- **📱 Mobile API**: Mobile-optimized enrichment endpoints
- **🌐 Multi-source Integration**: Additional data sources beyond TMDB/IMDB
- **⚡ Real-time Updates**: WebSocket-based progress updates

### Integration Roadmap

- **Elasticsearch Enhanced Search**: Full-text search integration
- **Redis Caching**: Advanced caching strategies
- **Celery Background Tasks**: Asynchronous processing
- **Admin Dashboard Enhancement**: Advanced monitoring and control

## 📞 Support & Maintenance

### Contact Information

- **Service Owner**: Movie Mate Development Team
- **Documentation**: `/docs/UNIFIED_MOVIE_ENRICHMENT_SERVICE_GUIDE.md`
- **API Documentation**: `/api/docs/` (Swagger)

### Maintenance Schedule

- **Daily**: Automated quality checks
- **Weekly**: Performance monitoring and optimization
- **Monthly**: API key rotation and service updates
- **Quarterly**: Feature updates and enhancements

---

## 🎉 Quick Start Example

```python
# Complete example: Enrich a movie with quality issues
from apps.movies.models import Movie
from apps.movies.services.unified_movie_enrichment_service import UnifiedMovieEnrichmentService

# Get a movie that needs enrichment
movie = Movie.objects.filter(
    quality_metrics__quality_score__lt=7.0
).first()

# Initialize service
service = UnifiedMovieEnrichmentService()

# Check current status
status = service.get_enrichment_status(movie)
print(f"Current quality: {status['quality_metrics']['quality_score']}/10")

# Perform quality-based enrichment
result = service.enrich_movie_by_quality_issues(movie)

# Show results
if result['success']:
    print(f"✅ Enrichment successful!")
    print(f"Quality improved: {result['quality_before']['quality_score']} → {result['quality_after']['quality_score']}")
    print(f"Improvements: {', '.join(result['improvements'])}")
else:
    print(f"❌ Enrichment failed: {result.get('error', 'Unknown error')}")
```

This unified service provides a complete solution for movie data enrichment, ensuring high-quality, comprehensive movie information for the Movie Mate platform. 🎬✨
