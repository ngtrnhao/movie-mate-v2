# Update Verification Guide - Model Normalization

## Overview
This guide helps verify that the views.py updates for model normalization are working correctly.

## Quick Testing Commands

### 1. Django Check
```bash
cd backend
python manage.py check
```
✅ Should pass without issues

### 2. Database Integrity Check
```bash
# Verify all models have been migrated
python manage.py showmigrations movies

# Check for any pending migrations
python manage.py makemigrations --dry-run
```

### 3. Test Admin API Endpoints

#### Dashboard Overview
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/movies/dashboard_overview/
```

#### Featured Movies
```bash
curl http://localhost:8000/api/movies/featured/
```

#### Production Metrics
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/admin/movies/production_metrics/
```

## Manual Testing Checklist

### ✅ Admin Dashboard
- [ ] Dashboard loads without errors
- [ ] Statistics show correct numbers
- [ ] Recent movies list displays
- [ ] Quality issues count is accurate

### ✅ Movie Management
- [ ] Movie list loads with pagination
- [ ] Filter by approval status works
- [ ] Filter by visibility status works
- [ ] Search functionality intact

### ✅ Admin Actions
- [ ] Toggle featured status
- [ ] Update priority (0-10 validation)
- [ ] Approve/reject movies
- [ ] Bulk operations work
- [ ] Visibility settings update

### ✅ Scheduling Features
- [ ] Schedule publication dates
- [ ] Schedule featured periods
- [ ] Campaign management
- [ ] Auto-scheduling works

### ✅ User Experience
- [ ] Featured movies display
- [ ] Trending movies work
- [ ] Top rated movies work
- [ ] User search functions
- [ ] Movie details load

## API Response Verification

### Check Admin Control Fields
```python
# In Django shell
from movies.models import Movie
movie = Movie.objects.select_related('admin_control').first()
print(f"Featured: {movie.admin_control.admin_featured}")
print(f"Priority: {movie.admin_control.admin_priority}")
print(f"Status: {movie.admin_control.approval_status}")
```

### Check Quality Metrics
```python
# In Django shell
from movies.models import Movie
movie = Movie.objects.select_related('quality_metrics').first()
print(f"Quality Score: {movie.quality_metrics.quality_score}")
print(f"Completeness: {movie.quality_metrics.content_completeness}")
print(f"Quality Met: {movie.quality_metrics.minimum_quality_met}")
```

### Check Scheduling
```python
# In Django shell
from movies.models import Movie
movie = Movie.objects.select_related('scheduling').first()
if hasattr(movie, 'scheduling'):
    print(f"Publish Date: {movie.scheduling.publish_date}")
    print(f"Featured From: {movie.scheduling.featured_from}")
```

## Performance Verification

### Query Count Check
Add this to test performance impact:

```python
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase

@override_settings(DEBUG=True)
def test_query_performance():
    from movies.views import OptimizedMovieViewSet

    # Reset queries
    connection.queries_log.clear()

    # Test production ready queryset
    viewset = OptimizedMovieViewSet()
    queryset = viewset.get_production_ready_queryset()[:10]
    list(queryset)  # Force evaluation

    print(f"Query count: {len(connection.queries)}")
    for query in connection.queries:
        print(query['sql'])
```

## Common Issues & Solutions

### ⚠️ Missing Related Objects
**Problem**: `RelatedObjectDoesNotExist` for admin_control or quality_metrics

**Solution**: Run data migration commands:
```bash
python manage.py migrate_admin_control_data
python manage.py migrate_quality_metrics_data
python manage.py migrate_scheduling_data
```

### ⚠️ Field Access Errors
**Problem**: `AttributeError: 'Movie' object has no attribute 'admin_featured'`

**Solution**: Update code to use `movie.admin_control.admin_featured`

### ⚠️ Query Performance Issues
**Problem**: Slow queries due to missing JOINs

**Solution**: Add proper `select_related()` calls:
```python
queryset = Movie.objects.select_related(
    'admin_control', 'quality_metrics', 'scheduling'
)
```

## Elasticsearch Verification

### Check Document Structure
```bash
curl -X GET "localhost:9200/movies/_mapping" | jq
```

### Verify Field Mapping
```python
from movies.documents import MovieDocument
doc = MovieDocument()
print(doc.prepare_approval_status(some_movie))
print(doc.prepare_admin_featured(some_movie))
```

## Cache Invalidation

Clear relevant caches after updates:
```python
from django.core.cache import cache
cache.clear()

# Or specific keys
cache.delete('featured_movies_v7_ultra_simple')
cache.delete('trending_movies_v4_production')
cache.delete('top_rated_movies_v4_production')
```

## Frontend Testing

### Test API Responses
Verify frontend compatibility by checking these endpoints return expected structure:

1. `/api/movies/featured/` - Featured movies
2. `/api/movies/trending/` - Trending movies
3. `/api/admin/movies/` - Admin movie list
4. `/api/admin/movies/production_metrics/` - Dashboard metrics

### Check Console Errors
Monitor browser console for:
- API errors
- Missing fields
- Type mismatches
- Serialization issues

## Rollback Plan

If issues are found, rollback steps:

1. **Database**: Restore from backup before migration
2. **Code**: Revert views.py changes
3. **Cache**: Clear all caches
4. **Frontend**: Restart frontend servers

## Success Criteria

✅ All tests pass
✅ No Django check errors
✅ Admin dashboard functional
✅ User features work
✅ Performance acceptable
✅ No console errors
✅ API responses correct format

## Contact

If issues arise, document:
1. Error messages
2. Steps to reproduce
3. Browser/environment details
4. API responses that differ from expected
