# 🗄️ Database Normalization Plan - Tách bảng Movie

## 🚨 **VẤN ĐỀ HIỆN TẠI**

Bảng `Movie` hiện tại có **quá nhiều concerns** được mix lại:

- ✅ **Basic movie data** (title, overview, release_date...)
- ❌ **Admin workflow** (approval_status, approved_by, approved_at...)
- ❌ **Quality metrics** (quality_score, content_completeness...)
- ❌ **Scheduling** (featured_from, featured_until, publish_date...)
- ❌ **Cached performance data** (cached ratings, combined scores...)

**Kết quả**: Table quá lớn, khó maintain, và vi phạm Single Responsibility Principle.

---

## 🎯 **CHIẾN LƯỢC NORMALIZATION**

### **1. Core Movie Table** 🎬 (Giữ lại)

**Chỉ chứa basic movie information**

```sql
CREATE TABLE movies_movie (
    id SERIAL PRIMARY KEY,

    -- Basic Info
    imdb_id VARCHAR(50) UNIQUE,
    tmdb_id VARCHAR(20) UNIQUE,
    movielens_id INTEGER UNIQUE,

    -- Titles & Content
    title VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    title_vi VARCHAR(255),
    original_title VARCHAR(255),
    slug VARCHAR(255) UNIQUE,
    overview_en TEXT,
    overview_vi TEXT,

    -- Basic Metadata
    release_date DATE,
    runtime INTEGER,
    status VARCHAR(50), -- RELEASED, UPCOMING, etc.
    is_adult BOOLEAN DEFAULT FALSE,

    -- Visual Assets
    poster_url VARCHAR(255),
    backdrop_url VARCHAR(255),

    -- System Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_synced TIMESTAMP
);
```

### **2. Movie Admin Control** 👨‍💼 (Tách riêng)

**Tất cả logic admin workflow**

```sql
CREATE TABLE movies_admin_control (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER REFERENCES movies_movie(id) ON DELETE CASCADE,

    -- Approval Workflow
    approval_status VARCHAR(20) DEFAULT 'PENDING',
        -- PENDING, APPROVED, REJECTED, NEEDS_REVIEW
    approved_by_id INTEGER REFERENCES users_user(id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    -- Visibility Control
    visibility_status VARCHAR(20) DEFAULT 'PUBLISHED',
        -- PUBLISHED, DRAFT, SCHEDULED, ARCHIVED, RESTRICTED
    is_published BOOLEAN DEFAULT TRUE,

    -- Admin Features
    admin_featured BOOLEAN DEFAULT FALSE,
    admin_priority INTEGER DEFAULT 0, -- 0-10 scale
    manual_override JSONB DEFAULT '{}',

    -- Targeting
    target_regions JSONB DEFAULT '[]',
    age_rating VARCHAR(10),
    content_warnings JSONB DEFAULT '[]',

    -- Audit Trail
    created_by_id INTEGER REFERENCES users_user(id),
    last_modified_by_id INTEGER REFERENCES users_user(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_admin_approval_status ON movies_admin_control(approval_status);
CREATE INDEX idx_admin_visibility ON movies_admin_control(visibility_status);
CREATE INDEX idx_admin_featured ON movies_admin_control(admin_featured);
CREATE INDEX idx_admin_priority ON movies_admin_control(admin_priority);
```

### **3. Movie Quality Metrics** 🏆 (Tách riêng)

**Quality calculation và content completeness**

```sql
CREATE TABLE movies_quality_metrics (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER REFERENCES movies_movie(id) ON DELETE CASCADE,

    -- Quality Scores
    quality_score DECIMAL(3,1), -- 0.0-10.0
    content_completeness DECIMAL(5,2) DEFAULT 0, -- 0.00-100.00%
    minimum_quality_met BOOLEAN DEFAULT TRUE,

    -- Quality Breakdown
    basic_info_score DECIMAL(3,1) DEFAULT 0, -- Title, overview, date
    visual_assets_score DECIMAL(3,1) DEFAULT 0, -- Poster, backdrop
    metadata_richness_score DECIMAL(3,1) DEFAULT 0, -- Cast, trailer, keywords
    rating_validity_score DECIMAL(3,1) DEFAULT 0, -- Valid ratings

    -- Quality Details
    quality_issues JSONB DEFAULT '[]', -- Array of issues found
    quality_suggestions JSONB DEFAULT '[]', -- Improvement suggestions
    last_quality_check TIMESTAMP,

    -- Automation
    auto_calculated BOOLEAN DEFAULT TRUE,
    calculation_version VARCHAR(10) DEFAULT '1.0',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_quality_score ON movies_quality_metrics(quality_score);
CREATE INDEX idx_quality_completeness ON movies_quality_metrics(content_completeness);
CREATE INDEX idx_quality_minimum_met ON movies_quality_metrics(minimum_quality_met);
```

### **4. Movie Scheduling** ⏰ (Tách riêng)

**Tất cả scheduling logic**

```sql
CREATE TABLE movies_scheduling (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER REFERENCES movies_movie(id) ON DELETE CASCADE,

    -- Publication Scheduling
    publish_date TIMESTAMP,
    unpublish_date TIMESTAMP,
    auto_publish BOOLEAN DEFAULT FALSE,
    auto_unpublish BOOLEAN DEFAULT FALSE,

    -- Featured Scheduling
    featured_from TIMESTAMP,
    featured_until TIMESTAMP,
    auto_feature BOOLEAN DEFAULT FALSE,
    auto_unfeature BOOLEAN DEFAULT FALSE,

    -- Recurring Schedules
    recurring_pattern JSONB, -- For seasonal content, etc.
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Status Tracking
    next_scheduled_action VARCHAR(50), -- publish, unpublish, feature, unfeature
    next_action_date TIMESTAMP,
    last_action_executed VARCHAR(50),
    last_action_date TIMESTAMP,

    -- Campaign Info
    campaign_name VARCHAR(255),
    campaign_type VARCHAR(50), -- marketing, seasonal, special
    campaign_priority INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_scheduling_publish_date ON movies_scheduling(publish_date);
CREATE INDEX idx_scheduling_featured_from ON movies_scheduling(featured_from);
CREATE INDEX idx_scheduling_next_action ON movies_scheduling(next_action_date);
CREATE INDEX idx_scheduling_campaign ON movies_scheduling(campaign_name);
```

### **5. Movie Cached Performance** 📈 (Cải thiện existing)

**Mở rộng ProductionMetrics hiện có**

```sql
-- Cải thiện bảng ProductionMetrics hiện có
ALTER TABLE movies_production_metrics ADD COLUMN IF NOT EXISTS
    -- Cached Rating Performance
    cached_imdb_rating DECIMAL(3,1),
    cached_imdb_votes INTEGER,
    cached_tmdb_rating DECIMAL(3,1),
    cached_tmdb_votes INTEGER,
    combined_rating_score DECIMAL(4,2),

    -- Performance Flags
    is_trending BOOLEAN DEFAULT FALSE,
    is_popular BOOLEAN DEFAULT FALSE,
    is_top_rated BOOLEAN DEFAULT FALSE,
    is_upcoming BOOLEAN DEFAULT FALSE,

    -- Cache Management
    ratings_last_updated TIMESTAMP,
    performance_last_calculated TIMESTAMP,
    cache_version VARCHAR(10) DEFAULT '1.0';

-- New indexes for performance
CREATE INDEX idx_metrics_cached_imdb ON movies_production_metrics(cached_imdb_rating);
CREATE INDEX idx_metrics_cached_tmdb ON movies_production_metrics(cached_tmdb_rating);
CREATE INDEX idx_metrics_combined_rating ON movies_production_metrics(combined_rating_score);
CREATE INDEX idx_metrics_trending ON movies_production_metrics(is_trending);
```

---

## 🔄 **MIGRATION STRATEGY**

### **Phase 1: Create New Tables**

```sql
-- 1. Tạo các bảng mới
CREATE TABLE movies_admin_control (...);
CREATE TABLE movies_quality_metrics (...);
CREATE TABLE movies_scheduling (...);

-- 2. Migrate data từ Movie table
INSERT INTO movies_admin_control (movie_id, approval_status, ...)
SELECT id, approval_status, ... FROM movies_movie;

INSERT INTO movies_quality_metrics (movie_id, quality_score, ...)
SELECT id, quality_score, ... FROM movies_movie;

INSERT INTO movies_scheduling (movie_id, publish_date, ...)
SELECT id, publish_date, ... FROM movies_movie;
```

### **Phase 2: Update Application Code**

```python
# Old code
movie = Movie.objects.get(id=123)
if movie.approval_status == 'APPROVED':
    # ...

# New code
movie = Movie.objects.select_related(
    'admin_control',
    'quality_metrics',
    'scheduling'
).get(id=123)

if movie.admin_control.approval_status == 'APPROVED':
    # ...
```

### **Phase 3: Update Serializers**

```python
class AdminMovieListSerializer(serializers.ModelSerializer):
    # Include related data
    admin_control = AdminControlSerializer()
    quality_metrics = QualityMetricsSerializer()
    scheduling = SchedulingSerializer()
    production_metrics = ProductionMetricsSerializer()

    class Meta:
        model = Movie
        fields = [
            # Basic movie fields
            'id', 'title', 'overview_en', 'release_date',
            # Related data
            'admin_control', 'quality_metrics',
            'scheduling', 'production_metrics'
        ]
```

### **Phase 4: Drop Old Columns**

```sql
-- Sau khi verify everything works
ALTER TABLE movies_movie
DROP COLUMN approval_status,
DROP COLUMN approved_by_id,
DROP COLUMN quality_score,
DROP COLUMN content_completeness,
DROP COLUMN publish_date,
DROP COLUMN featured_from,
-- ... drop all migrated columns
```

---

## 🎯 **LỢI ÍCH CỦA NORMALIZATION**

| Aspect                | Before                 | After                    |
| --------------------- | ---------------------- | ------------------------ |
| **Table Size**        | 🔴 1 huge table        | ✅ 5 focused tables      |
| **Query Performance** | 🔴 Full table scans    | ✅ Targeted queries      |
| **Maintenance**       | 🔴 Hard to modify      | ✅ Easy to extend        |
| **Caching**           | 🔴 Cache entire object | ✅ Cache by concern      |
| **Services**          | 🔴 All mixed together  | ✅ Separate services     |
| **Testing**           | 🔴 Complex test setup  | ✅ Unit test per service |

### **Performance Benefits**

- ✅ **Faster admin queries**: Chỉ load admin_control khi cần
- ✅ **Better indexing**: Specialized indexes per table
- ✅ **Reduced lock contention**: Updates isolated by concern
- ✅ **Easier caching**: Cache admin data vs movie data separately

### **Development Benefits**

- ✅ **Clear separation**: Each service owns its data
- ✅ **Easier testing**: Mock individual concerns
- ✅ **Better migrations**: Small, focused schema changes
- ✅ **Team collaboration**: Frontend/Backend can work on different concerns

---

## 🛠️ **IMPLEMENTATION TIMELINE**

| Week       | Task                               | Owner    |
| ---------- | ---------------------------------- | -------- |
| **Week 1** | Create new table schemas           | Backend  |
| **Week 2** | Build migration scripts            | Backend  |
| **Week 3** | Update Django models & serializers | Backend  |
| **Week 4** | Update admin APIs                  | Backend  |
| **Week 5** | Update frontend components         | Frontend |
| **Week 6** | Testing & performance validation   | Both     |
| **Week 7** | Deploy to staging                  | DevOps   |
| **Week 8** | Production deployment              | DevOps   |

**Tổng thời gian**: ~2 tháng cho complete normalization

---

## ❓ **DECISION POINTS**

1. **Có nên migrate tất cả cùng lúc?**

   - 👍 **Phased approach**: Migrate từng concern một
   - 👎 **Big bang**: Nguy hiểm, khó rollback

2. **Có nên keep backwards compatibility?**

   - 👍 **Yes**: Tạo property methods để access qua movie
   - 👎 **Clean break**: Force update toàn bộ codebase

3. **Performance impact?**
   - 🤔 **JOINs**: Có thể chậm hơn denormalized data
   - ✅ **select_related**: Django ORM optimize well
   - ✅ **Specialized indexes**: Better than single table

**Recommendation**: Phased migration với backwards compatibility trong 1-2 months transition period.
