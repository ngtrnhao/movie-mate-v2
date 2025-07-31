# 🗄️ ERD Diagram - Movie Recommendation System

## 📊 Tổng quan hệ thống

Hệ thống Movie Recommendation được thiết kế với kiến trúc microservices, bao gồm các module chính:

- **Users**: Quản lý người dùng và authentication
- **Movies**: Quản lý phim và metadata
- **Metadata**: Quản lý genres và categories
- **Recommendations**: Hệ thống gợi ý phim
- **Subscriptions**: Quản lý thanh toán và gói dịch vụ

---

## 🎯 Core Entities & Relationships

### 1. **USERS MODULE** 👥

```mermaid
erDiagram
    User {
        int id PK
        string username UK
        string email UK
        string first_name
        string last_name
        string avatar_url
        text bio
        date birth_date
        int age
        string gender
        string location
        string age_group
        string occupation
        string zip_code
        boolean is_email_verified
        boolean is_google_account
        string user_type
        datetime created_at
        datetime updated_at
    }

    UserFavoriteGenre {
        int id PK
        int user_id FK
        int genre_id FK
        datetime created_at
        datetime updated_at
    }

    UserFavoriteMovie {
        int id PK
        int user_id FK
        int movie_id FK
        datetime created_at
        datetime updated_at
    }

    Watchlist {
        int id PK
        int user_id FK
        string name
        datetime created_at
        datetime updated_at
    }

    WatchlistItem {
        int id PK
        int watchlist_id FK
        int movie_id FK
        string status
        datetime created_at
        datetime updated_at
    }

    SearchHistory {
        int id PK
        int user_id FK
        string search_query
        int search_results_count
        datetime created_at
    }

    EmailVerificationToken {
        int id PK
        int user_id FK
        string token UK
        datetime created_at
        datetime expires_at
    }

    PasswordResetToken {
        int id PK
        int user_id FK
        string token UK
        datetime created_at
        datetime expires_at
    }

    User ||--o{ UserFavoriteGenre : "has"
    User ||--o{ UserFavoriteMovie : "has"
    User ||--o{ Watchlist : "has"
    User ||--o{ SearchHistory : "has"
    User ||--o{ EmailVerificationToken : "has"
    User ||--o{ PasswordResetToken : "has"
    Watchlist ||--o{ WatchlistItem : "contains"
```

### 2. **MOVIES MODULE** 🎬

```mermaid
erDiagram
    Movie {
        int id PK
        string imdb_id UK
        int movielens_id UK
        string title
        string title_en
        string title_vi
        string original_title
        string slug UK
        text overview_en
        text overview_vi
        date release_date
        string poster_url
        string backdrop_url
        string tmdb_id UK
        int runtime
        string status
        boolean is_popular
        boolean is_top_rated
        boolean is_upcoming
        boolean is_adult
        decimal cached_imdb_rating
        int cached_imdb_votes
        decimal cached_tmdb_rating
        int cached_tmdb_votes
        decimal combined_rating_score
        datetime created_at
        datetime updated_at
        datetime last_synced
    }

    MovieMetadata {
        int id PK
        int movie_id FK
        bigint budget
        bigint revenue
        text tagline
        string homepage
        json keywords
        json production_companies
        json production_countries
        json spoken_languages
        datetime created_at
        datetime updated_at
    }

    MovieGenre {
        int id PK
        int movie_id FK
        int genre_id FK
        datetime created_at
        datetime updated_at
    }

    MovieTrailer {
        int id PK
        int movie_id FK
        string title
        string youtube_key
        string type
        datetime created_at
    }

    MovieImage {
        int id PK
        int movie_id FK
        string image_url
        string type
        int width
        int height
        decimal aspect_ratio
        datetime created_at
    }

    MovieRating {
        int id PK
        int movie_id FK
        decimal imdb_rating
        int imdb_votes
        int metacritic_rating
        decimal rotten_tomatoes_rating
        int rotten_tomatoes_votes
        decimal tmdb_rating
        int tmdb_votes
        decimal film_affinity_rating
        int film_affinity_votes
        datetime created_at
        datetime updated_at
    }

    MovieCast {
        int id PK
        int movie_id FK
        string name
        string role
        string main_character
        json all_characters
        int order
        string job
        string category
        string imdb_id
        string profile_path
        int birth_year
        int death_year
        json primary_profession
        json known_for_titles
        int tmdb_id
        text biography
        string place_of_birth
        int gender
        decimal popularity
        datetime created_at
        datetime updated_at
    }

    MovieReview {
        int id PK
        int movie_id FK
        int user_id FK
        string external_username
        string title
        text content
        decimal rating
        int parent_review_id FK
        int reply_to_user_id FK
        string review_type
        string language
        boolean is_public
        boolean is_spoiler
        float spoiler_confidence
        json spoiler_detected_patterns
        string spoiler_suggested_action
        text spoiler_explanation
        boolean auto_marked
        boolean is_approved
        int moderated_by_id FK
        datetime moderated_at
        text moderation_reason
        int helpful_votes
        int total_votes
        string external_review_id
        string source
        datetime external_published_at
        datetime created_at
        datetime updated_at
    }

    ReviewVote {
        int id PK
        int review_id FK
        int user_id FK
        string vote_type
        datetime created_at
        datetime updated_at
    }

    ReviewReport {
        int id PK
        int review_id FK
        int reported_by_id FK
        string reason
        text description
        datetime created_at
    }

    MovieBoxOffice {
        int id PK
        int movie_id FK
        bigint budget
        bigint domestic_gross
        bigint foreign_gross
        bigint worldwide_gross
        bigint opening_weekend_gross
        datetime created_at
        datetime updated_at
    }

    Movie ||--|| MovieMetadata : "has"
    Movie ||--o{ MovieGenre : "belongs_to"
    Movie ||--o{ MovieTrailer : "has"
    Movie ||--o{ MovieImage : "has"
    Movie ||--o{ MovieRating : "has"
    Movie ||--o{ MovieCast : "has"
    Movie ||--o{ MovieReview : "has"
    Movie ||--|| MovieBoxOffice : "has"
    MovieReview ||--o{ ReviewVote : "has"
    MovieReview ||--o{ ReviewReport : "has"
    MovieReview ||--o{ MovieReview : "replies_to"
```

### 3. **ADMIN CONTROL MODULE** 👨‍💼

```mermaid
erDiagram
    MovieAdminControl {
        int id PK
        int movie_id FK
        string approval_status
        int approved_by_id FK
        datetime approved_at
        text rejection_reason
        string visibility_status
        boolean is_published
        boolean admin_featured
        int admin_priority
        json manual_override
        json target_regions
        string age_rating
        json content_warnings
        int created_by_id FK
        int last_modified_by_id FK
        datetime created_at
        datetime updated_at
    }

    MovieQualityMetrics {
        int id PK
        int movie_id FK
        decimal quality_score
        decimal content_completeness
        boolean minimum_quality_met
        decimal basic_info_score
        decimal visual_assets_score
        decimal metadata_richness_score
        decimal rating_validity_score
        json quality_issues
        json quality_suggestions
        datetime last_quality_check
        boolean auto_calculated
        string calculation_version
        datetime created_at
        datetime updated_at
    }

    MovieScheduling {
        int id PK
        int movie_id FK
        datetime publish_date
        datetime unpublish_date
        boolean auto_publish
        boolean auto_unpublish
        datetime featured_from
        datetime featured_until
        boolean auto_feature
        boolean auto_unfeature
        json recurring_pattern
        string timezone
        string next_scheduled_action
        datetime next_action_date
        string last_action_executed
        datetime last_action_date
        string campaign_name
        string campaign_type
        int campaign_priority
        datetime created_at
        datetime updated_at
    }

    ProductionMetrics {
        int id PK
        int movie_id FK
        int homepage_views
        int detail_page_views
        int trailer_plays
        decimal click_through_rate
        decimal engagement_rate
        decimal trailer_completion_rate
        int mobile_views
        int desktop_views
        int tablet_views
        decimal performance_score
        decimal trending_score
        string trending_category
        int review_count
        decimal average_user_rating
        int user_favorites_count
        int user_watchlist_count
        int user_shares_count
        int user_likes_count
        datetime last_interaction_date
        datetime last_featured_date
        datetime created_at
        datetime updated_at
        datetime last_calculated_at
        boolean auto_calculated
        string calculation_version
    }

    ModerationConfig {
        int id PK
        float auto_mark_threshold
        float flag_for_review_threshold
        float suggest_warning_threshold
        boolean learning_enabled
        float learning_rate
        int min_feedback_count
        boolean auto_moderate_enabled
        boolean require_approval_for_auto_marked
        float send_to_moderation_queue_threshold
        boolean notify_moderators_on_auto_mark
        boolean daily_report_enabled
        float accuracy_target
        float false_positive_limit
        int created_by_id FK
        datetime created_at
        datetime updated_at
        boolean is_active
    }

    ModerationFeedback {
        int id PK
        int review_id FK
        int moderator_id FK
        float original_confidence
        string original_suggested_action
        boolean original_is_spoiler
        string feedback_type
        string moderator_decision
        boolean is_spoiler_correct
        text notes
        string difficulty_level
        int time_spent_seconds
        boolean used_for_learning
        float learning_impact_score
        datetime created_at
        datetime updated_at
    }

    UserInteraction {
        int id PK
        int movie_id FK
        int user_id FK
        string session_id
        string action
        string interaction_type
        url page_url
        url referrer
        text user_agent
        string screen_resolution
        string viewport_size
        json metadata
        datetime timestamp
        datetime processed_at
        int duration_seconds
        boolean is_unique_session
    }

    Movie ||--|| MovieAdminControl : "has"
    Movie ||--|| MovieQualityMetrics : "has"
    Movie ||--|| MovieScheduling : "has"
    Movie ||--|| ProductionMetrics : "has"
    Movie ||--o{ UserInteraction : "tracks"
    MovieReview ||--o{ ModerationFeedback : "has"
```

### 4. **METADATA MODULE** 📚

```mermaid
erDiagram
    Genre {
        int id PK
        string name
        string language
        string slug UK
        text description
        datetime created_at
        datetime updated_at
    }

    GenreSummary {
        int id PK
        int genre_id FK
        string language
        int movie_count
        json latest_movie_data
        datetime last_updated
    }

    Genre ||--|| GenreSummary : "has"
    Genre ||--o{ MovieGenre : "categorizes"
```

### 5. **RECOMMENDATIONS MODULE** 🎯

```mermaid
erDiagram
    UserPreference {
        int id PK
        int user_id FK
        json genre_preferences
        json actor_preferences
        json director_preferences
        json year_preferences
        string demographic_cluster
        string behavior_cluster
        float novelty_preference
        float diversity_preference
        float recency_preference
        int rating_count
        float average_rating
        float rating_variance
        int interaction_count
        datetime created_at
        datetime updated_at
        datetime last_calculated
    }

    UserSimilarity {
        int id PK
        int user1_id FK
        int user2_id FK
        string similarity_type
        float similarity_score
        int common_ratings_count
        string calculation_method
        float confidence
        datetime created_at
        datetime updated_at
    }

    MovieSimilarity {
        int id PK
        int movie1_id FK
        int movie2_id FK
        string similarity_type
        float similarity_score
        float genre_similarity
        float cast_similarity
        float director_similarity
        float year_similarity
        float rating_similarity
        datetime created_at
    }

    RecommendationResult {
        int id PK
        int user_id FK
        int movie_id FK
        string recommendation_type
        string context
        float predicted_rating
        float confidence_score
        float novelty_score
        int rank
        float score
        json explanation
        boolean was_clicked
        boolean was_rated
        boolean was_watched
        string user_feedback
        datetime created_at
        datetime expires_at
    }

    DemographicCluster {
        int id PK
        string cluster_id UK
        string name
        text description
        int age_range_min
        int age_range_max
        string primary_gender
        json common_occupations
        json geographic_regions
        json preferred_genres
        float average_rating
        float rating_variance
        int user_count
        datetime created_at
        datetime updated_at
    }

    RecommendationMetrics {
        int id PK
        date date
        string recommendation_type
        int total_recommendations
        int unique_users
        int unique_movies
        float average_predicted_rating
        float average_actual_rating
        float rmse
        float mae
        float click_through_rate
        float conversion_rate
        float average_rating_given
        float intra_list_diversity
        float novelty_score
        float catalog_coverage
        datetime created_at
    }

    User ||--|| UserPreference : "has"
    User ||--o{ UserSimilarity : "similar_to"
    User ||--o{ RecommendationResult : "receives"
    Movie ||--o{ MovieSimilarity : "similar_to"
    Movie ||--o{ RecommendationResult : "recommended_in"
```

### 6. **SUBSCRIPTIONS MODULE** 💳

```mermaid
erDiagram
    PaymentTransaction {
        int id PK
        int user_id FK
        string plan
        decimal amount
        string paypal_order_id UK
        string status
        json raw_data
        datetime start_date
        datetime end_date
        datetime created_at
        datetime updated_at
    }

    User ||--o{ PaymentTransaction : "has"
```

---

## 🔗 Cross-Module Relationships

### **Core Relationships:**

1. **User ↔ Movie** (Many-to-Many)

   - `UserFavoriteMovie` (Favorites)
   - `WatchlistItem` (Watchlist)
   - `MovieReview` (Reviews)
   - `UserInteraction` (Tracking)

2. **Movie ↔ Genre** (Many-to-Many)

   - `MovieGenre` (Categorization)

3. **User ↔ Genre** (Many-to-Many)

   - `UserFavoriteGenre` (Preferences)

4. **Movie ↔ Cast** (One-to-Many)

   - `MovieCast` (Cast information)

5. **Movie ↔ Review** (One-to-Many)
   - `MovieReview` (User reviews)
   - `ReviewVote` (Voting system)
   - `ReviewReport` (Moderation)

### **Admin & Analytics Relationships:**

1. **Movie ↔ Admin Control** (One-to-One)

   - `MovieAdminControl` (Workflow management)
   - `MovieQualityMetrics` (Quality assessment)
   - `MovieScheduling` (Publication scheduling)
   - `ProductionMetrics` (Performance analytics)

2. **Review ↔ Moderation** (One-to-Many)
   - `ModerationFeedback` (Quality control)
   - `ModerationConfig` (System configuration)

### **Recommendation Relationships:**

1. **User ↔ User** (Many-to-Many)

   - `UserSimilarity` (Collaborative filtering)

2. **Movie ↔ Movie** (Many-to-Many)

   - `MovieSimilarity` (Content-based filtering)

3. **User ↔ Movie** (Many-to-Many)
   - `RecommendationResult` (Generated recommendations)

---

## 📈 Database Indexes & Performance

### **Primary Indexes:**

- All `id` fields (Primary Keys)
- All `user_id`, `movie_id`, `genre_id` (Foreign Keys)
- Unique constraints on `email`, `username`, `imdb_id`, `tmdb_id`

### **Performance Indexes:**

- Composite indexes for common queries
- Partial indexes for filtered data
- Temporal indexes for date-based queries
- Full-text search indexes for content

### **Caching Strategy:**

- Redis for session management
- Elasticsearch for movie search
- Application-level caching for popular queries

---

## 🎯 Key Features Supported

### **User Management:**

- Authentication & Authorization
- Profile management with demographics
- Email verification & password reset
- Google OAuth integration

### **Movie Management:**

- Multi-language support (EN/VI)
- Rich metadata (cast, crew, ratings)
- Media assets (posters, trailers, images)
- Quality assessment & moderation

### **Recommendation System:**

- Collaborative filtering
- Content-based filtering
- Demographic filtering
- Hybrid algorithms
- Performance tracking

### **Admin Features:**

- Content moderation workflow
- Quality metrics calculation
- Publication scheduling
- Analytics dashboard

### **Subscription Management:**

- Multiple plan tiers
- PayPal integration
- Usage tracking

---

## 🔧 Technical Specifications

### **Database:**

- **Primary**: PostgreSQL
- **Cache**: Redis
- **Search**: Elasticsearch
- **File Storage**: Local/Cloud (configurable)

### **Architecture:**

- Django REST Framework backend
- React frontend
- Celery for background tasks
- Docker containerization

### **Security:**

- JWT authentication
- CSRF protection
- Rate limiting
- Data encryption

### **Performance:**

- Database optimization
- Caching strategies
- CDN for static assets
- Load balancing ready

---

_ERD Diagram này thể hiện cấu trúc database hoàn chỉnh của hệ thống Movie Recommendation, hỗ trợ đầy đủ các tính năng từ user management đến advanced recommendation algorithms._
