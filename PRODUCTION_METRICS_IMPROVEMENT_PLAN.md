# 🚀 Kế hoạch cải thiện Production Metrics System

## 🎯 **Phase 1: Model Optimization (Week 1)**

### **1.1 Thêm trending_category field**

#### **Migration 1: Thêm trending_category**

```python
# backend/apps/movies/migrations/0043_add_trending_category.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('movies', '0042_add_production_metrics_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='productionmetrics',
            name='trending_category',
            field=models.CharField(
                choices=[
                    ('viral', 'Viral'),
                    ('hot', 'Hot'),
                    ('rising', 'Rising'),
                    ('stable', 'Stable')
                ],
                default='stable',
                max_length=20,
                help_text='Trending category based on recent activity'
            ),
        ),
        migrations.AddIndex(
            model_name='productionmetrics',
            index=models.Index(fields=['trending_category'], name='idx_trending_category'),
        ),
    ]
```

#### **Update ProductionMetrics Model**

```python
# backend/apps/movies/models.py (ProductionMetrics class)

# Thêm field mới:
trending_category = models.CharField(
    max_length=20,
    choices=[
        ('viral', 'Viral'),
        ('hot', 'Hot'),
        ('rising', 'Rising'),
        ('stable', 'Stable')
    ],
    default='stable',
    db_index=True,
    help_text="Trending category based on recent activity"
)

# Thêm method helper:
def get_trending_category_display_with_emoji(self):
    """Get trending category with emoji for UI display"""
    emoji_map = {
        'viral': '🔥 Viral',
        'hot': '🌟 Hot',
        'rising': '📈 Rising',
        'stable': '😐 Stable'
    }
    return emoji_map.get(self.trending_category, '😐 Stable')

@classmethod
def update_trending_categories(cls):
    """Bulk update trending categories for all metrics"""
    metrics = cls.objects.all()

    for metric in metrics:
        if metric.trending_score >= 80:
            metric.trending_category = 'viral'
        elif metric.trending_score >= 60:
            metric.trending_category = 'hot'
        elif metric.trending_score >= 30:
            metric.trending_category = 'rising'
        else:
            metric.trending_category = 'stable'

    cls.objects.bulk_update(metrics, ['trending_category'])
```

### **1.2 Data Migration để populate trending_category**

```python
# backend/apps/movies/migrations/0044_populate_trending_category.py
from django.db import migrations

def populate_trending_category(apps, schema_editor):
    ProductionMetrics = apps.get_model('movies', 'ProductionMetrics')

    for metric in ProductionMetrics.objects.all():
        if metric.trending_score >= 80:
            metric.trending_category = 'viral'
        elif metric.trending_score >= 60:
            metric.trending_category = 'hot'
        elif metric.trending_score >= 30:
            metric.trending_category = 'rising'
        else:
            metric.trending_category = 'stable'
        metric.save()

def reverse_populate_trending_category(apps, schema_editor):
    ProductionMetrics = apps.get_model('movies', 'ProductionMetrics')
    ProductionMetrics.objects.update(trending_category='stable')

class Migration(migrations.Migration):
    dependencies = [
        ('movies', '0043_add_trending_category'),
    ]

    operations = [
        migrations.RunPython(
            populate_trending_category,
            reverse_populate_trending_category,
        ),
    ]
```

### **1.3 Remove unused fields (Optional - Phase 2)**

```python
# backend/apps/movies/migrations/0045_remove_unused_fields.py
# (Có thể thực hiện sau khi confirm không còn sử dụng)

class Migration(migrations.Migration):
    dependencies = [
        ('movies', '0044_populate_trending_category'),
    ]

    operations = [
        # Remove unused fields
        migrations.RemoveField(model_name='productionmetrics', name='trailer_completion_rate'),
        migrations.RemoveField(model_name='productionmetrics', name='last_featured_date'),
        migrations.RemoveField(model_name='productionmetrics', name='total_featured_days'),
        migrations.RemoveField(model_name='productionmetrics', name='first_published_date'),
        migrations.RemoveField(model_name='productionmetrics', name='region_performance'),
        migrations.RemoveField(model_name='productionmetrics', name='language_preferences'),
        migrations.RemoveField(model_name='productionmetrics', name='positive_review_ratio'),
        migrations.RemoveField(model_name='productionmetrics', name='bounce_rate'),
        migrations.RemoveField(model_name='productionmetrics', name='session_duration_avg'),
        migrations.RemoveField(model_name='productionmetrics', name='return_visitor_rate'),
    ]
```

## 🔧 **Phase 2: Services Synchronization (Week 2)**

### **2.1 Update ProductionMetricsService**

```python
# backend/apps/movies/services/production_metrics_service.py

class ProductionMetricsService:
    # Add trending category constants
    TRENDING_THRESHOLDS = {
        'viral': 80,
        'hot': 60,
        'rising': 30,
        'stable': 0
    }

    def _calculate_trending_category(self, trending_score: float) -> str:
        """Calculate trending category based on score"""
        if trending_score >= self.TRENDING_THRESHOLDS['viral']:
            return 'viral'
        elif trending_score >= self.TRENDING_THRESHOLDS['hot']:
            return 'hot'
        elif trending_score >= self.TRENDING_THRESHOLDS['rising']:
            return 'rising'
        else:
            return 'stable'

    def _calculate_trending_metrics(self, movie: Movie, current_metrics: Dict, interaction_metrics: Dict) -> Dict:
        """🔥 ENHANCED: Calculate trending metrics with category"""

        # ... existing trending calculation logic ...

        # Calculate trending category
        trending_category = self._calculate_trending_category(trending_score)

        return {
            'is_trending': is_trending,
            'trending_score': round(trending_score, 2),
            'trending_category': trending_category,  # NEW: Add category
            'recent_activity_score': recent_activity,
            'recent_users_score': recent_users
        }

    def _save_production_metrics(self, production_metrics: ProductionMetrics, metrics_data: Dict):
        """Enhanced save with trending_category"""
        try:
            with transaction.atomic():
                # Ensure trending_category is included
                if 'trending_category' not in metrics_data:
                    metrics_data['trending_category'] = self._calculate_trending_category(
                        metrics_data.get('trending_score', 0)
                    )

                # Update existing record
                for key, value in metrics_data.items():
                    if hasattr(production_metrics, key):
                        setattr(production_metrics, key, value)

                production_metrics.save()
                logger.info(f"✅ Production metrics updated for movie {production_metrics.movie.id} - Category: {metrics_data['trending_category']}")

        except Exception as e:
            logger.error(f"❌ Error saving production metrics for movie {production_metrics.movie.id}: {str(e)}")
            raise

    @classmethod
    def bulk_update_trending_categories(cls) -> Dict:
        """Bulk update trending categories for all movies"""
        service = cls()
        updated_count = 0

        metrics_qs = ProductionMetrics.objects.all()

        for metrics in metrics_qs:
            trending_category = service._calculate_trending_category(metrics.trending_score)
            if metrics.trending_category != trending_category:
                metrics.trending_category = trending_category
                metrics.save(update_fields=['trending_category'])
                updated_count += 1

        return {
            'total_checked': metrics_qs.count(),
            'updated_count': updated_count
        }
```

### **2.2 Update UserDataCollectionService**

```python
# backend/apps/movies/services/user_data_collection_service.py

class UserDataCollectionService:

    def _calculate_trending_category(self, trending_score: float) -> str:
        """Consistent trending category calculation with ProductionMetricsService"""
        if trending_score >= 80:
            return 'viral'
        elif trending_score >= 60:
            return 'hot'
        elif trending_score >= 30:
            return 'rising'
        else:
            return 'stable'

    def _calculate_detailed_metrics_from_db(self, movie, interactions):
        """🔥 ENHANCED: Include trending_category in calculations"""

        # ... existing calculation logic ...

        # Calculate trending category
        trending_category = self._calculate_trending_category(production_metrics.trending_score)

        # Update trending category if changed
        if production_metrics.trending_category != trending_category:
            production_metrics.trending_category = trending_category

        # ... rest of the method ...
```

### **2.3 Add Management Command**

```python
# backend/apps/movies/management/commands/sync_trending_categories.py

from django.core.management.base import BaseCommand
from apps.movies.services.production_metrics_service import ProductionMetricsService

class Command(BaseCommand):
    help = 'Sync trending categories for all movies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write('🧪 DRY RUN MODE - No changes will be made')

        self.stdout.write('🔄 Syncing trending categories...')

        result = ProductionMetricsService.bulk_update_trending_categories()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Sync complete: {result["updated_count"]}/{result["total_checked"]} updated'
            )
        )
```

## 🎨 **Phase 3: Frontend Enhancement (Week 3)**

### **3.1 Thêm tracking vào các components chưa có**

#### **MovieCard Component Enhancement**

```javascript
// frontend/src/components/movies/movie-card/index.jsx

import { useRef, useEffect } from "react";
import useUserTracking from "../../../hooks/useUserTracking";

const MovieCard = ({ movie, index, source = "unknown" }) => {
  const cardRef = useRef(null);
  const { trackHomepageView, trackMovieClick, createViewObserver } =
    useUserTracking();

  useEffect(() => {
    if (cardRef.current && movie?.id) {
      // Auto track view when card appears
      const observer = createViewObserver(cardRef.current, movie.id, {
        section: source,
        position: index,
        movie_title: movie.title,
      });

      return () => observer?.disconnect();
    }
  }, [movie?.id, index, source]);

  const handleClick = () => {
    if (movie?.id) {
      trackMovieClick(movie.id, {
        source: source,
        position: index,
        movie_title: movie.title,
        trending_category:
          movie.production_metrics?.trending_category || "stable",
      });
    }
  };

  // ... rest of component
};
```

#### **MovieGrid Component Enhancement**

```javascript
// frontend/src/components/movies/movie-grid/MovieGrid.jsx

import useUserTracking from "../../../hooks/useUserTracking";

const MovieGrid = ({ movies, gridType = "standard" }) => {
  const { trackInteraction } = useUserTracking();

  const handleSort = (sortType) => {
    trackInteraction({
      action: "sort",
      metadata: {
        sort_type: sortType,
        grid_type: gridType,
        page_section: "movie_grid",
      },
    });
  };

  const handleFilter = (filterType, filterValue) => {
    trackInteraction({
      action: "filter",
      metadata: {
        filter_type: filterType,
        filter_value: filterValue,
        grid_type: gridType,
      },
    });
  };

  // ... rest of component
};
```

### **3.2 Enhanced useUserTracking Hook**

```javascript
// frontend/src/hooks/useUserTracking.js

// Add new tracking methods:
const trackFilter = (filterType, filterValue, metadata = {}) => {
  userInteractionService.trackInteraction(null, "filter", {
    filter_type: filterType,
    filter_value: filterValue,
    interaction_type: "filter_selection",
    ...metadata,
  });
};

const trackSort = (sortType, metadata = {}) => {
  userInteractionService.trackInteraction(null, "sort", {
    sort_type: sortType,
    interaction_type: "sort_selection",
    ...metadata,
  });
};

const trackPagination = (page, totalPages, metadata = {}) => {
  userInteractionService.trackInteraction(null, "pagination", {
    current_page: page,
    total_pages: totalPages,
    interaction_type: "page_navigation",
    ...metadata,
  });
};

// Return new methods
return {
  // ... existing methods ...
  trackFilter,
  trackSort,
  trackPagination,
  // ... rest
};
```

### **3.3 Homepage Enhancement**

```javascript
// frontend/src/pages/Home/index.jsx

import useUserTracking from "../../hooks/useUserTracking";

const HomePage = () => {
  const { trackInteraction } = useUserTracking();

  useEffect(() => {
    // Track homepage visit
    trackInteraction({
      action: "page_view",
      metadata: {
        page: "homepage",
        timestamp: new Date().toISOString(),
      },
    });
  }, []);

  // ... rest of component
};
```

## 📊 **Phase 4: Admin Dashboard Enhancement (Week 4)**

### **4.1 Enhanced Admin API Endpoints**

```python
# backend/apps/movies/views.py (AdminMovieViewSet)

@action(detail=False, methods=['get'])
def trending_analytics(self, request):
    """Get detailed trending analytics for admin dashboard"""
    try:
        from django.db.models import Count, Avg

        # Trending category distribution
        trending_distribution = ProductionMetrics.objects.values('trending_category').annotate(
            count=Count('id'),
            avg_score=Avg('trending_score'),
            avg_views=Avg('homepage_views')
        ).order_by('-count')

        # Recent trending changes
        recent_viral = ProductionMetrics.objects.filter(
            trending_category='viral',
            updated_at__gte=timezone.now() - timedelta(hours=24)
        ).select_related('movie')[:10]

        # Performance by category
        category_performance = ProductionMetrics.objects.values('trending_category').annotate(
            avg_engagement=Avg('engagement_rate'),
            avg_ctr=Avg('click_through_rate'),
            avg_performance=Avg('performance_score')
        )

        return Response({
            'status': 'success',
            'data': {
                'trending_distribution': list(trending_distribution),
                'recent_viral_movies': [
                    {
                        'movie_id': pm.movie.id,
                        'title': pm.movie.title,
                        'trending_score': float(pm.trending_score),
                        'category': pm.trending_category
                    } for pm in recent_viral
                ],
                'category_performance': list(category_performance)
            }
        })

    except Exception as e:
        logger.error(f"Error in trending analytics: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@action(detail=False, methods=['get'])
def real_time_metrics(self, request):
    """Get real-time interaction metrics"""
    try:
        from apps.movies.models import UserInteraction

        # Last hour activity
        last_hour = timezone.now() - timedelta(hours=1)
        recent_interactions = UserInteraction.objects.filter(
            timestamp__gte=last_hour
        )

        # Top movies by recent activity
        top_movies = recent_interactions.values(
            'movie__id', 'movie__title'
        ).annotate(
            interaction_count=Count('id')
        ).order_by('-interaction_count')[:10]

        # Activity by action type
        activity_breakdown = recent_interactions.values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'status': 'success',
            'data': {
                'total_interactions_last_hour': recent_interactions.count(),
                'top_movies': list(top_movies),
                'activity_breakdown': list(activity_breakdown),
                'timestamp': timezone.now().isoformat()
            }
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### **4.2 Frontend Admin Dashboard Enhancement**

```javascript
// frontend/src/pages/Admin/components/TrendingAnalytics.jsx

import { useState, useEffect } from "react";
import {
  getTrendingAnalytics,
  getRealTimeMetrics,
} from "../../../api/adminMovieService";

const TrendingAnalytics = () => {
  const [trendingData, setTrendingData] = useState(null);
  const [realTimeData, setRealTimeData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [trending, realTime] = await Promise.all([
        getTrendingAnalytics(),
        getRealTimeMetrics(),
      ]);

      setTrendingData(trending.data);
      setRealTimeData(realTime.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading analytics...</div>;

  return (
    <div className="space-y-6">
      {/* Trending Category Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">📈 Trending Categories</h3>
        <div className="grid grid-cols-4 gap-4">
          {trendingData?.trending_distribution?.map((category) => (
            <div key={category.trending_category} className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {category.count}
              </div>
              <div className="text-sm text-gray-500">
                {category.trending_category}
              </div>
              <div className="text-xs text-gray-400">
                Avg: {category.avg_score?.toFixed(1)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Real-time Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">
          ⚡ Real-time Activity (Last Hour)
        </h3>
        <div className="text-3xl font-bold text-green-600 mb-2">
          {realTimeData?.total_interactions_last_hour || 0}
        </div>
        <div className="text-sm text-gray-500">Total Interactions</div>

        {/* Top Movies */}
        <div className="mt-4">
          <h4 className="font-medium mb-2">🔥 Most Active Movies</h4>
          <div className="space-y-2">
            {realTimeData?.top_movies?.slice(0, 5).map((movie, index) => (
              <div key={movie.movie__id} className="flex justify-between">
                <span className="truncate">{movie.movie__title}</span>
                <span className="font-medium">{movie.interaction_count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrendingAnalytics;
```

## 🔧 **Phase 5: Management Commands & Automation**

### **5.1 Automated Daily Reports**

```python
# backend/apps/movies/management/commands/daily_metrics_report.py

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from apps.movies.models import ProductionMetrics, UserInteraction
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Generate and send daily metrics report'

    def handle(self, *args, **options):
        yesterday = datetime.now() - timedelta(days=1)

        # Generate report data
        report_data = self.generate_report(yesterday)

        # Send email report
        self.send_email_report(report_data)

        self.stdout.write(
            self.style.SUCCESS('✅ Daily report generated and sent')
        )

    def generate_report(self, date):
        # Daily metrics summary
        # Trending changes
        # Performance alerts
        # User engagement statistics
        pass

    def send_email_report(self, data):
        # Send to admin team
        pass
```

### **5.2 Performance Monitoring Command**

```python
# backend/apps/movies/management/commands/monitor_performance.py

class Command(BaseCommand):
    help = 'Monitor system performance and send alerts'

    def handle(self, *args, **options):
        # Check for performance issues
        # Detect trending anomalies
        # Monitor system health
        # Send alerts if needed
        pass
```

## 📋 **Testing Plan**

### **Phase 1 Testing:**

- [ ] Migration tests (trending_category field)
- [ ] Model validation tests
- [ ] Data migration verification

### **Phase 2 Testing:**

- [ ] Service synchronization tests
- [ ] Trending category calculation tests
- [ ] Performance benchmark tests

### **Phase 3 Testing:**

- [ ] Frontend tracking integration tests
- [ ] User interaction flow tests
- [ ] Cross-browser compatibility

### **Phase 4 Testing:**

- [ ] Admin API endpoint tests
- [ ] Dashboard functionality tests
- [ ] Real-time updates tests

## 🎯 **Success Metrics**

### **Performance Improvements:**

- [ ] 40% reduction in ProductionMetrics storage
- [ ] 30% faster query performance
- [ ] 100% trending_category coverage

### **Data Quality:**

- [ ] Consistent trending calculations across services
- [ ] Real-time metrics accuracy > 95%
- [ ] Zero data inconsistencies

### **User Experience:**

- [ ] Complete user interaction tracking
- [ ] Rich admin dashboard insights
- [ ] Automated monitoring and alerts

**Timeline: 4 weeks total**
**Resources needed: 1 Full-stack Developer**
**Risk level: Low (non-breaking changes)**
