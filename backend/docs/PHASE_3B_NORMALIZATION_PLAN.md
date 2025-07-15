# 🗄️ Phase 3B: Continue Database Normalization Plan

## 📋 **CURRENT STATUS**

### ✅ **COMPLETED**

- `MovieAdminControl` table created (migration 0038)
- `ProductionMetrics` table exists and comprehensive
- AdminControl data migration successful

### ❌ **REMAINING WORK**

- Movie model still contains old fields (need cleanup)
- `MovieQualityMetrics` not created
- `MovieScheduling` not created
- Cached rating data needs organization

---

## 🎯 **PHASE 3B TASKS**

### **Task 1: Create MovieQualityMetrics Table**

**Fields to migrate from Movie:**

```python
# FROM movies_movie
quality_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
content_completeness = models.DecimalField(max_digits=5, decimal_places=2, default=0)
minimum_quality_met = models.BooleanField(default=True)
```

**NEW MovieQualityMetrics model:**

```python
class MovieQualityMetrics(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name='quality_metrics')

    # Quality Scores
    quality_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    content_completeness = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    minimum_quality_met = models.BooleanField(default=True)

    # Quality Breakdown (for future calculation services)
    basic_info_score = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    visual_assets_score = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    metadata_richness_score = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    rating_validity_score = models.DecimalField(max_digits=3, decimal_places=1, default=0)

    # Quality Details
    quality_issues = models.JSONField(default=list, blank=True)
    quality_suggestions = models.JSONField(default=list, blank=True)
    last_quality_check = models.DateTimeField(null=True, blank=True)

    # Automation flags
    auto_calculated = models.BooleanField(default=True)
    calculation_version = models.CharField(max_length=10, default='1.0')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### **Task 2: Create MovieScheduling Table**

**Fields to migrate from Movie:**

```python
# FROM movies_movie
publish_date = models.DateTimeField(null=True, blank=True)
unpublish_date = models.DateTimeField(null=True, blank=True)
featured_from = models.DateTimeField(null=True, blank=True)
featured_until = models.DateTimeField(null=True, blank=True)
```

**NEW MovieScheduling model:**

```python
class MovieScheduling(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name='scheduling')

    # Publication Scheduling
    publish_date = models.DateTimeField(null=True, blank=True)
    unpublish_date = models.DateTimeField(null=True, blank=True)
    auto_publish = models.BooleanField(default=False)
    auto_unpublish = models.BooleanField(default=False)

    # Featured Scheduling
    featured_from = models.DateTimeField(null=True, blank=True)
    featured_until = models.DateTimeField(null=True, blank=True)
    auto_feature = models.BooleanField(default=False)
    auto_unfeature = models.BooleanField(default=False)

    # Recurring Schedules (for future)
    recurring_pattern = models.JSONField(default=dict, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')

    # Status Tracking
    next_scheduled_action = models.CharField(max_length=50, null=True, blank=True)
    next_action_date = models.DateTimeField(null=True, blank=True)
    last_action_executed = models.CharField(max_length=50, null=True, blank=True)
    last_action_date = models.DateTimeField(null=True, blank=True)

    # Campaign Info (for future marketing features)
    campaign_name = models.CharField(max_length=255, null=True, blank=True)
    campaign_type = models.CharField(max_length=50, null=True, blank=True)
    campaign_priority = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### **Task 3: Enhance ProductionMetrics with Cached Ratings**

**Move cached rating fields from Movie to ProductionMetrics:**

```python
# FROM movies_movie - MOVE TO ProductionMetrics
cached_imdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
cached_imdb_votes = models.IntegerField(null=True, blank=True)
cached_tmdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
cached_tmdb_votes = models.IntegerField(null=True, blank=True)
combined_rating_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
```

**Add to existing ProductionMetrics:**

```python
# ADD TO movies_production_metrics
cached_imdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
cached_imdb_votes = models.IntegerField(null=True, blank=True)
cached_tmdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
cached_tmdb_votes = models.IntegerField(null=True, blank=True)
combined_rating_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

# Performance flags
is_trending = models.BooleanField(default=False)
is_popular = models.BooleanField(default=False)
is_top_rated = models.BooleanField(default=False)
is_upcoming = models.BooleanField(default=False)

# Cache management
ratings_last_updated = models.DateTimeField(null=True, blank=True)
performance_last_calculated = models.DateTimeField(null=True, blank=True)
cache_version = models.CharField(max_length=10, default='1.0')
```

---

## 🔄 **MIGRATION STRATEGY**

### **Step 1: Create New Models**

1. Create `MovieQualityMetrics` model
2. Create `MovieScheduling` model
3. Enhance `ProductionMetrics` model

### **Step 2: Generate and Run Migrations**

1. `python manage.py makemigrations --name="create_quality_metrics_table"`
2. `python manage.py makemigrations --name="create_scheduling_table"`
3. `python manage.py makemigrations --name="enhance_production_metrics"`

### **Step 3: Data Migration Commands**

```python
# migrate_quality_metrics_data.py
python manage.py migrate_quality_metrics_data

# migrate_scheduling_data.py
python manage.py migrate_scheduling_data

# migrate_cached_ratings_data.py
python manage.py migrate_cached_ratings_data
```

### **Step 4: Update Serializers & APIs**

1. Create `QualityMetricsSerializer`
2. Create `SchedulingSerializer`
3. Update `ProductionMetricsSerializer`
4. Update `AdminMovieSerializer` to include new nested data

### **Step 5: Update Frontend**

1. Update utility functions in `MovieManagement.jsx`
2. Add support for new nested structures
3. Maintain backward compatibility

### **Step 6: Remove Old Fields** (Final cleanup)

```python
# After validation, remove from Movie model:
- quality_score
- content_completeness
- minimum_quality_met
- publish_date
- unpublish_date
- featured_from
- featured_until
- cached_imdb_rating
- cached_imdb_votes
- cached_tmdb_rating
- cached_tmdb_votes
- combined_rating_score
```

---

## ⚡ **EXPECTED BENEFITS**

### **Performance**

- Smaller Movie table (faster queries)
- Specialized indexes per concern
- Optimized caching strategies

### **Maintainability**

- Clear separation of concerns
- Easier to add new features
- Better code organization

### **Scalability**

- Independent scaling per table
- Targeted optimization possible
- Cleaner database design

---

## 🚨 **CRITICAL CONSIDERATIONS**

### **Data Integrity**

- All 717,980 movies must be migrated
- Zero data loss tolerance
- Comprehensive validation required

### **Backward Compatibility**

- APIs must continue working
- Frontend must not break
- Legacy access patterns maintained

### **Performance During Migration**

- Batch processing (1000-5000 records)
- Monitor memory usage
- Minimal downtime strategy

---

## 📝 **NEXT IMMEDIATE ACTIONS**

1. **Create MovieQualityMetrics model** → Generate migration
2. **Create MovieScheduling model** → Generate migration
3. **Create data migration commands** → Safe batch processing
4. **Test on subset of data** → Validate integrity
5. **Full migration execution** → Production deployment
6. **Update serializers & APIs** → Maintain compatibility
7. **Frontend integration** → Enhanced utility functions
8. **Remove old fields** → Final cleanup

**Estimated Timeline**: 2-3 days for complete normalization
**Risk Level**: Medium (well-tested approach from AdminControl success)
