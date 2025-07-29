# Movie Recommendation System - Complete Implementation Guide

## Overview

This document describes the fully implemented recommendation system for Movie Mate v2, featuring demographic filtering, collaborative filtering, and hybrid algorithms with automatic user clustering and real-time recommendation generation.

## System Architecture

### Backend Components

1. **Models** (`apps/recommendations/models.py`)

   - `UserPreference`: Stores user preferences and characteristics
   - `UserSimilarity`: Precomputed user similarity matrix
   - `MovieSimilarity`: Precomputed movie similarity matrix
   - `RecommendationResult`: Generated recommendations with metadata
   - `DemographicCluster`: User demographic clusters
   - `RecommendationMetrics`: Performance tracking

2. **Services** (`apps/recommendations/services.py`)

   - `CollaborativeFilteringService`: User-based collaborative filtering
   - `EnhancedDemographicFilteringService`: Demographic-based recommendations
   - `HybridRecommendationService`: Combines multiple algorithms

3. **API Endpoints** (`apps/recommendations/views.py`)
   - `/api/recommendations/api/personalized/` - Personalized recommendations
   - `/api/recommendations/api/collaborative/` - Collaborative filtering
   - `/api/recommendations/api/demographic/` - Demographic filtering
   - `/api/recommendations/api/hybrid/` - Hybrid recommendations
   - `/api/recommendations/api/feedback/` - Feedback submission
   - `/api/recommendations/api/profile/` - User recommendation profile

### Frontend Components

1. **State Management** (`frontend/src/store/slices/recommendationSlice.js`)

   - Redux slice for recommendation state management
   - Async thunks for API calls
   - Caching and error handling

2. **API Service** (`frontend/src/api/recommendationService.js`)

   - API communication layer
   - Helper functions for data formatting
   - Interaction tracking

3. **Components**
   - `HeroBannerRecommendation`: Hero banner with personalized movie
   - `RecommendForYou`: Recommendation carousel
   - Automatic recommendation loading and display

## Features Implemented

### ✅ Automatic User Setup

- **Django Signals**: Automatically create user preferences after registration
- **Demographic Clustering**: Auto-assign users to demographic clusters
- **Background Tasks**: Generate initial recommendations immediately

### ✅ Recommendation Algorithms

- **Demographic Filtering**: Based on age, gender, occupation
- **Collaborative Filtering**: User-to-user similarity
- **Hybrid Recommendations**: Combines multiple algorithms
- **Personalized Selection**: Automatically chooses best algorithm for each user

### ✅ Real-time Integration

- **Frontend State Management**: Redux-based recommendation state
- **API Integration**: Real-time data fetching from backend
- **Fallback Handling**: Graceful degradation to popular movies
- **Interaction Tracking**: User clicks and ratings tracked

### ✅ Background Processing

- **Celery Tasks**: Automatic recommendation updates
- **Similarity Calculations**: User and movie similarity updates
- **Cache Management**: Automatic cache warming and cleanup
- **Performance Monitoring**: Automatic metrics collection

### ✅ Optimization Features

- **Immediate Results**: New users get recommendations instantly
- **Progressive Enhancement**: Recommendations improve with user data
- **Caching**: API responses cached for performance
- **Batch Processing**: Efficient bulk operations

## Setup Instructions

### 1. Database Migration

```bash
# Activate virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run migrations
python manage.py makemigrations recommendations
python manage.py migrate
```

### 2. Initial System Setup

```bash
# Setup recommendation system
python manage.py setup_initial_recommendations

# Optional: Force recreate everything
python manage.py setup_initial_recommendations --force-recreate

# Optional: Only setup users, skip recommendation generation
python manage.py setup_initial_recommendations --users-only
```

### 3. Start Background Tasks

```bash
# Start Celery worker
celery -A config worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A config beat --loglevel=info
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm start
```

## Usage Guide

### For Developers

#### Adding New Recommendation Types

1. **Add to Models** (`models.py`):

```python
RECOMMENDATION_TYPES = [
    # ... existing types
    ('your_new_type', 'Your New Type'),
]
```

2. **Implement Service Method**:

```python
def generate_your_new_recommendations(self, user, limit=20, context='homepage'):
    # Your algorithm implementation
    return movies_list
```

3. **Add API Endpoint**:

```python
@action(detail=False, methods=['get'])
def your_new_type(self, request):
    # Implementation
    pass
```

#### Customizing Algorithms

**Demographic Filtering Weights**:

```python
# In EnhancedDemographicFilteringService
def calculate_cluster_preferences(self, cluster):
    # Customize how cluster preferences are calculated
    pass
```

**Collaborative Filtering Parameters**:

```python
# In CollaborativeFilteringService
self.min_common_ratings = 5  # Minimum ratings to consider similarity
self.similarity_threshold = 0.1  # Minimum similarity score
```

### For Users

#### How Recommendations Work

1. **New Users**:

   - Get popular movies immediately
   - Assigned to demographic cluster if age/gender provided
   - Recommendations improve as they rate movies

2. **Existing Users**:

   - Personalized recommendations based on ratings
   - Similar user recommendations (collaborative filtering)
   - Demographic-based suggestions
   - Hybrid combination of all methods

3. **Real-time Updates**:
   - Recommendations update when users rate movies
   - Profile changes trigger re-clustering
   - Background tasks keep recommendations fresh

## API Usage Examples

### Get Personalized Recommendations

```javascript
// Frontend
import { useDispatch } from "react-redux";
import { loadPersonalizedRecommendations } from "../store/slices/recommendationSlice";

const dispatch = useDispatch();
dispatch(
  loadPersonalizedRecommendations({
    context: "homepage",
    limit: 20,
  })
);
```

```python
# Backend
GET /api/recommendations/api/personalized/?context=homepage&limit=20
```

### Submit Feedback

```javascript
// Frontend
import { submitFeedback } from "../store/slices/recommendationSlice";

dispatch(
  submitFeedback({
    movieId: 123,
    recommendationType: "personalized",
    context: "homepage",
    feedbackType: "like",
    action: "clicked",
  })
);
```

## Performance Monitoring

### Built-in Metrics

The system automatically tracks:

- Click-through rates by recommendation type
- User engagement metrics
- Algorithm performance
- Cache hit rates

### Accessing Metrics

```bash
# View recommendation stats
curl /api/recommendations/api/stats/

# View user recommendation profile
curl -H "Authorization: Bearer <token>" /api/recommendations/api/profile/
```

### Celery Task Monitoring

```bash
# View active tasks
celery -A config inspect active

# View scheduled tasks
celery -A config inspect scheduled

# View task stats
celery -A config inspect stats
```

## Troubleshooting

### Common Issues

1. **No Recommendations Showing**

   ```bash
   # Check if setup was run
   python manage.py setup_initial_recommendations

   # Check demographic clusters exist
   python manage.py shell
   >>> from apps.recommendations.models import DemographicCluster
   >>> DemographicCluster.objects.count()
   ```

2. **Recommendations Not Updating**

   ```bash
   # Check Celery is running
   celery -A config worker --loglevel=info

   # Manually generate recommendations
   python manage.py shell
   >>> from apps.users.tasks import generate_recommendations_for_active_users
   >>> generate_recommendations_for_active_users.delay()
   ```

3. **Frontend Not Loading Recommendations**

   ```javascript
   // Check Redux state
   console.log(store.getState().recommendations);

   // Check API calls in network tab
   // Verify authentication token is present
   ```

### Debug Mode

Enable debug logging in Django settings:

```python
LOGGING = {
    'loggers': {
        'apps.recommendations': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Future Enhancements

### Planned Features

1. **Advanced ML Models**

   - Deep learning recommendation models
   - Content-based filtering using movie features
   - Real-time model training

2. **Enhanced Personalization**

   - Mood-based recommendations
   - Context-aware suggestions (time, device, etc.)
   - Social recommendations from friends

3. **Analytics Dashboard**
   - Real-time recommendation performance
   - A/B testing framework
   - User segmentation analysis

### Contributing

When adding new features:

1. Follow the existing service pattern
2. Add comprehensive tests
3. Update this documentation
4. Consider performance impact
5. Add appropriate caching

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review Django logs: `tail -f logs/django.log`
3. Check Celery logs: `tail -f logs/celery.log`
4. Review frontend console for errors

---

**Last Updated**: December 2024
**Version**: 2.0.0
**Authors**: Development Team
