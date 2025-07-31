# PostgreSQL Table Schema cho StarUML

## Movie Recommendation System

### 🎨 Hướng dẫn vẽ ERD trong StarUML

#### Bước 1: Tạo Project

```
File → New → Project
Tên: "Movie_Recommendation_ERD"
```

#### Bước 2: Tạo ERD Diagram

```
Add Diagram → Entity Relationship Diagram
Tên: "Movie_Recommendation_Database"
```

#### Bước 3: Cài đặt màu sắc

- **Users App**: #4A90E2 (Blue)
- **Movies App**: #7ED321 (Green)
- **Metadata App**: #F5A623 (Yellow)
- **Recommendations App**: #9013FE (Purple)
- **Subscriptions App**: #D0021B (Red)

---

## 📋 USERS APP - Chi tiết từng bảng

### 1. **users_users** (User Entity)

**Màu sắc**: #4A90E2 (Blue)
**Kích thước**: 140x100 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
password: VARCHAR(128) NOT NULL
last_login: TIMESTAMP NULL
is_superuser: BOOLEAN NOT NULL DEFAULT FALSE
username: VARCHAR(150) NOT NULL
first_name: VARCHAR(150) NOT NULL DEFAULT ''
last_name: VARCHAR(150) NOT NULL DEFAULT ''
email: VARCHAR(254) NOT NULL
is_staff: BOOLEAN NOT NULL DEFAULT FALSE
is_active: BOOLEAN NOT NULL DEFAULT TRUE
date_joined: TIMESTAMP NOT NULL DEFAULT NOW()
avatar_url: VARCHAR(500) NULL
bio: TEXT NULL
birth_date: DATE NULL
age: INTEGER NULL
gender: VARCHAR(10) NULL
location: VARCHAR(255) NULL
age_group: VARCHAR(20) NULL
occupation: VARCHAR(50) NULL
zip_code: VARCHAR(10) NULL
is_email_verified: BOOLEAN NOT NULL DEFAULT FALSE
is_google_account: BOOLEAN NOT NULL DEFAULT FALSE
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
user_type: VARCHAR(20) NOT NULL DEFAULT 'member'
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (email)
- UNIQUE (username)
- CHECK (gender IN ('M', 'F', 'O'))
- CHECK (user_type IN ('member', 'premium_basic', 'premium_standard', 'premium_vip'))

**Indexes:**

- idx_users_username (username)
- idx_users_email (email)
- idx_users_age_group (age_group)
- idx_users_occupation (occupation)
- idx_users_zip_code (zip_code)

---

### 2. **users_users_favorite_genres** (UserFavoriteGenre Entity)

**Màu sắc**: #CCCCCC (Gray - Junction Table)
**Kích thước**: 100x60 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id)
genre_id: INTEGER NOT NULL (Foreign Key → metadata_genre.id)
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (user_id, genre_id)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE
- FOREIGN KEY (genre_id) REFERENCES metadata_genre(id) ON DELETE CASCADE

**Indexes:**

- idx_user_favorite_genre_user (user_id)
- idx_user_favorite_genre_genre (genre_id)
- idx_user_favorite_genre_created (created_at)

---

### 3. **users_users_favorite_movies** (UserFavoriteMovie Entity)

**Màu sắc**: #CCCCCC (Gray - Junction Table)
**Kích thước**: 100x60 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id)
movie_id: INTEGER NOT NULL (Foreign Key → movies_movie.id)
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (user_id, movie_id)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE
- FOREIGN KEY (movie_id) REFERENCES movies_movie(id) ON DELETE CASCADE

**Indexes:**

- idx_user_favorite_movie_user (user_id)
- idx_user_favorite_movie_movie (movie_id)
- idx_user_favorite_movie_created (created_at)

---

### 4. **users_watchlist** (Watchlist Entity)

**Màu sắc**: #4A90E2 (Blue)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id)
name: VARCHAR(255) NOT NULL
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (user_id, name)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE

**Indexes:**

- idx_watchlist_user (user_id)
- idx_watchlist_created (created_at)

---

### 5. **users_watchlistitem** (WatchlistItem Entity)

**Màu sắc**: #4A90E2 (Blue)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
watchlist_id: INTEGER NOT NULL (Foreign Key → users_watchlist.id)
movie_id: INTEGER NOT NULL (Foreign Key → movies_movie.id)
status: VARCHAR(20) NOT NULL DEFAULT 'PLANNED'
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (watchlist_id, movie_id)
- FOREIGN KEY (watchlist_id) REFERENCES users_watchlist(id) ON DELETE CASCADE
- FOREIGN KEY (movie_id) REFERENCES movies_movie(id) ON DELETE CASCADE
- CHECK (status IN ('PLANNED', 'WATCHING', 'COMPLETED', 'ON_HOLD', 'DROPPED'))

**Indexes:**

- idx_watchlistitem_watchlist_movie (watchlist_id, movie_id)
- idx_watchlistitem_status (status)
- idx_watchlistitem_created (created_at)

---

### 6. **users_searchhistory** (SearchHistory Entity)

**Màu sắc**: #4A90E2 (Blue)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id)
search_query: VARCHAR(255) NOT NULL
search_results_count: INTEGER NOT NULL
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE

**Indexes:**

- idx_searchhistory_user_created (user_id, created_at)

---

### 7. **users_emailverificationtoken** (EmailVerificationToken Entity)

**Màu sắc**: #4A90E2 (Blue)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id)
token: VARCHAR(100) NOT NULL
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
expires_at: TIMESTAMP NOT NULL
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (token)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE

**Indexes:**

- idx_emailverificationtoken_token (token)
- idx_emailverificationtoken_user (user_id)
- idx_emailverificationtoken_expires (expires_at)

---

### 8. **users_passwordresettoken** (PasswordResetToken Entity)

**Màu sắc**: #4A90E2 (Blue)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id)
token: VARCHAR(100) NOT NULL
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
expires_at: TIMESTAMP NOT NULL
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (token)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE

**Indexes:**

- idx_passwordresettoken_token (token)
- idx_passwordresettoken_user (user_id)
- idx_passwordresettoken_expires (expires_at)

---

## 🔗 Relationships trong Users App

### One-to-Many (1:N)

```
User → Watchlist (1:N)
User → SearchHistory (1:N)
User → EmailVerificationToken (1:N)
User → PasswordResetToken (1:N)
Watchlist → WatchlistItem (1:N)
```

### Many-to-Many (N:N)

```
User ↔ Genre (through UserFavoriteGenre)
User ↔ Movie (through UserFavoriteMovie)
```

### Foreign Key Relationships

```
UserFavoriteGenre.user_id → User.id
UserFavoriteGenre.genre_id → Genre.id
UserFavoriteMovie.user_id → User.id
UserFavoriteMovie.movie_id → Movie.id
Watchlist.user_id → User.id
WatchlistItem.watchlist_id → Watchlist.id
WatchlistItem.movie_id → Movie.id
SearchHistory.user_id → User.id
EmailVerificationToken.user_id → User.id
PasswordResetToken.user_id → User.id
```

---

## 📝 Hướng dẫn vẽ trong StarUML

### Bước 1: Vẽ User Entity

1. Tạo Entity với tên "User"
2. Màu sắc: #4A90E2
3. Kích thước: 140x100
4. Thêm tất cả attributes với kiểu PostgreSQL
5. Đánh dấu Primary Key (id)
6. Thêm constraints và indexes

### Bước 2: Vẽ Junction Tables

1. Tạo UserFavoriteGenre và UserFavoriteMovie
2. Màu sắc: #CCCCCC
3. Kích thước: 100x60
4. Đánh dấu Composite Primary Keys

### Bước 3: Vẽ Supporting Entities

1. Tạo Watchlist, WatchlistItem, SearchHistory
2. Màu sắc: #4A90E2
3. Kích thước: 120x80
4. Thêm Foreign Key relationships

### Bước 4: Vẽ Token Entities

1. Tạo EmailVerificationToken, PasswordResetToken
2. Màu sắc: #4A90E2
3. Kích thước: 120x80
4. Thêm unique constraints

### Bước 5: Vẽ Relationships

1. Vẽ One-to-Many relationships với mũi tên
2. Vẽ Many-to-Many relationships qua junction tables
3. Thêm cardinality (1, N, M)
4. Thêm relationship names

---

---

## 📋 METADATA APP - Chi tiết từng bảng

### 1. **metadata_genre** (Genre Entity)

**Màu sắc**: #F5A623 (Yellow)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
name: VARCHAR(100) NOT NULL
language: VARCHAR(10) NULL
slug: VARCHAR(100) NOT NULL
description: TEXT NULL
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (name, language)
- UNIQUE (slug)

**Indexes:**

- idx_genre_name (name)
- idx_genre_language (language)
- idx_genre_slug (slug)
- idx_genre_lang_name (language, name)
- idx_genre_lang_slug (language, slug)
- idx_genre_lang_with_movies (language) WHERE language IS NOT NULL

---

### 2. **metadata_genre_summary** (GenreSummary Entity)

**Màu sắc**: #F5A623 (Yellow)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
genre_id: INTEGER NOT NULL (Foreign Key → metadata_genre.id)
language: VARCHAR(10) NOT NULL
movie_count: INTEGER NOT NULL DEFAULT 0
latest_movie_data: JSONB NULL
last_updated: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (genre_id, language)
- FOREIGN KEY (genre_id) REFERENCES metadata_genre(id) ON DELETE CASCADE

**Indexes:**

- idx_genresummary_language (language)
- idx_genresummary_lang_count (language, movie_count)
- idx_genresummary_updated (last_updated)

---

## 🔗 Relationships trong Metadata App

### One-to-One (1:1)

```
Genre → GenreSummary (1:1)
```

### Foreign Key Relationships

```
GenreSummary.genre_id → Genre.id
```

---

## 📝 Hướng dẫn vẽ Metadata App trong StarUML

### Bước 1: Vẽ Genre Entity

1. Tạo Entity với tên "Genre"
2. Màu sắc: #F5A623 (Yellow)
3. Kích thước: 120x80
4. Thêm tất cả attributes với kiểu PostgreSQL
5. Đánh dấu Primary Key (id)
6. Thêm unique constraints

### Bước 2: Vẽ GenreSummary Entity

1. Tạo Entity với tên "GenreSummary"
2. Màu sắc: #F5A623 (Yellow)
3. Kích thước: 120x80
4. Thêm Foreign Key relationship với Genre

### Bước 3: Vẽ Relationship

1. Vẽ One-to-One relationship giữa Genre và GenreSummary
2. Thêm cardinality (1:1)
3. Thêm relationship name: "has_summary"

---

---

## 📋 SUBSCRIPTIONS APP - Chi tiết từng bảng

### 1. **subscriptions_paymenttransaction** (PaymentTransaction Entity)

**Màu sắc**: #D0021B (Red)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id)
plan: VARCHAR(20) NOT NULL
amount: DECIMAL(8,2) NOT NULL
paypal_order_id: VARCHAR(128) NOT NULL
status: VARCHAR(32) NOT NULL
raw_data: JSONB NOT NULL
start_date: TIMESTAMP NOT NULL
end_date: TIMESTAMP NOT NULL
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (paypal_order_id)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE
- CHECK (plan IN ('basic', 'standard', 'vip'))

**Indexes:**

- idx_paymenttransaction_user (user_id)
- idx_paymenttransaction_paypal_order_id (paypal_order_id)
- idx_paymenttransaction_status (status)
- idx_paymenttransaction_created (created_at)

---

## 🔗 Relationships trong Subscriptions App

### One-to-Many (1:N)

```
User → PaymentTransaction (1:N)
```

### Foreign Key Relationships

```
PaymentTransaction.user_id → User.id
```

---

## 📝 Hướng dẫn vẽ Subscriptions App trong StarUML

### Bước 1: Vẽ PaymentTransaction Entity

1. Tạo Entity với tên "PaymentTransaction"
2. Màu sắc: #D0021B (Red)
3. Kích thước: 120x80
4. Thêm tất cả attributes với kiểu PostgreSQL
5. Đánh dấu Primary Key (id)
6. Thêm unique constraint cho paypal_order_id

### Bước 2: Vẽ Relationship

1. Vẽ One-to-Many relationship từ User đến PaymentTransaction
2. Thêm cardinality (1:N)
3. Thêm relationship name: "has_payments"

---

---

## 📋 RECOMMENDATIONS APP - Chi tiết từng bảng

### 1. **recommendations_user_preference** (UserPreference Entity)

**Màu sắc**: #9013FE (Purple)
**Kích thước**: 140x100 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id, unique)
genre_preferences: JSONB NOT NULL DEFAULT '{}'
actor_preferences: JSONB NOT NULL DEFAULT '{}'
director_preferences: JSONB NOT NULL DEFAULT '{}'
year_preferences: JSONB NOT NULL DEFAULT '{}'
demographic_cluster: VARCHAR(50) NULL
behavior_cluster: VARCHAR(50) NULL
novelty_preference: FLOAT NOT NULL DEFAULT 0.5
diversity_preference: FLOAT NOT NULL DEFAULT 0.5
recency_preference: FLOAT NOT NULL DEFAULT 0.5
rating_count: INTEGER NOT NULL DEFAULT 0
average_rating: FLOAT NOT NULL DEFAULT 0.0
rating_variance: FLOAT NOT NULL DEFAULT 0.0
interaction_count: INTEGER NOT NULL DEFAULT 0
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
last_calculated: TIMESTAMP NULL
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (user_id)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE
- CHECK (novelty_preference >= 0.0 AND novelty_preference <= 1.0)
- CHECK (diversity_preference >= 0.0 AND diversity_preference <= 1.0)
- CHECK (recency_preference >= 0.0 AND recency_preference <= 1.0)

**Indexes:**

- idx_user_preference_demographic_cluster (demographic_cluster)
- idx_user_preference_behavior_cluster (behavior_cluster)
- idx_user_preference_rating_count (rating_count)
- idx_user_preference_average_rating (average_rating)
- idx_user_preference_last_calculated (last_calculated)

---

### 2. **recommendations_user_similarity** (UserSimilarity Entity)

**Màu sắc**: #CCCCCC (Gray - Junction Table)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user1_id: INTEGER NOT NULL (Foreign Key → users_users.id)
user2_id: INTEGER NOT NULL (Foreign Key → users_users.id)
similarity_type: VARCHAR(20) NOT NULL
similarity_score: FLOAT NOT NULL
common_ratings_count: INTEGER NOT NULL DEFAULT 0
calculation_method: VARCHAR(50) NOT NULL DEFAULT 'pearson'
confidence: FLOAT NOT NULL DEFAULT 1.0
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (user1_id, user2_id, similarity_type)
- FOREIGN KEY (user1_id) REFERENCES users_users(id) ON DELETE CASCADE
- FOREIGN KEY (user2_id) REFERENCES users_users(id) ON DELETE CASCADE
- CHECK (similarity_score >= -1.0 AND similarity_score <= 1.0)
- CHECK (similarity_type IN ('collaborative', 'demographic', 'behavioral', 'hybrid'))

**Indexes:**

- idx_user_similarity_user1_type_score (user1_id, similarity_type, similarity_score)
- idx_user_similarity_user2_type_score (user2_id, similarity_type, similarity_score)
- idx_user_similarity_score_confidence (similarity_score, confidence)
- idx_user_similarity_updated (updated_at)

---

### 3. **recommendations_movie_similarity** (MovieSimilarity Entity)

**Màu sắc**: #CCCCCC (Gray - Junction Table)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
movie1_id: INTEGER NOT NULL (Foreign Key → movies_movie.id)
movie2_id: INTEGER NOT NULL (Foreign Key → movies_movie.id)
similarity_type: VARCHAR(20) NOT NULL
similarity_score: FLOAT NOT NULL
genre_similarity: FLOAT NOT NULL DEFAULT 0.0
cast_similarity: FLOAT NOT NULL DEFAULT 0.0
director_similarity: FLOAT NOT NULL DEFAULT 0.0
year_similarity: FLOAT NOT NULL DEFAULT 0.0
rating_similarity: FLOAT NOT NULL DEFAULT 0.0
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (movie1_id, movie2_id, similarity_type)
- FOREIGN KEY (movie1_id) REFERENCES movies_movie(id) ON DELETE CASCADE
- FOREIGN KEY (movie2_id) REFERENCES movies_movie(id) ON DELETE CASCADE
- CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0)
- CHECK (similarity_type IN ('content', 'collaborative', 'genre', 'cast', 'hybrid'))

**Indexes:**

- idx_movie_similarity_movie1_type_score (movie1_id, similarity_type, similarity_score)
- idx_movie_similarity_movie2_type_score (movie2_id, similarity_type, similarity_score)
- idx_movie_similarity_score (similarity_score)
- idx_movie_similarity_genre (genre_similarity)
- idx_movie_similarity_cast (cast_similarity)

---

### 4. **recommendations_result** (RecommendationResult Entity)

**Màu sắc**: #9013FE (Purple)
**Kích thước**: 140x100 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
user_id: INTEGER NOT NULL (Foreign Key → users_users.id)
movie_id: INTEGER NOT NULL (Foreign Key → movies_movie.id)
recommendation_type: VARCHAR(20) NOT NULL
context: VARCHAR(20) NOT NULL DEFAULT 'homepage'
predicted_rating: FLOAT NULL
confidence_score: FLOAT NOT NULL DEFAULT 0.5
novelty_score: FLOAT NOT NULL DEFAULT 0.5
rank: INTEGER NOT NULL
score: FLOAT NOT NULL
explanation: JSONB NOT NULL DEFAULT '{}'
was_clicked: BOOLEAN NOT NULL DEFAULT FALSE
was_rated: BOOLEAN NOT NULL DEFAULT FALSE
was_watched: BOOLEAN NOT NULL DEFAULT FALSE
user_feedback: VARCHAR(20) NULL
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
expires_at: TIMESTAMP NOT NULL
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (user_id, movie_id, recommendation_type, context)
- FOREIGN KEY (user_id) REFERENCES users_users(id) ON DELETE CASCADE
- FOREIGN KEY (movie_id) REFERENCES movies_movie(id) ON DELETE CASCADE
- CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0)
- CHECK (recommendation_type IN ('collaborative', 'demographic', 'content_based', 'trending', 'popular', 'hybrid', 'similar_users', 'genre_based'))
- CHECK (context IN ('homepage', 'after_rating', 'profile', 'genre_explorer', 'similar_movies', 'onboarding'))
- CHECK (user_feedback IN ('like', 'dislike', 'not_interested'))

**Indexes:**

- idx_recommendation_result_user_type_rank (user_id, recommendation_type, rank)
- idx_recommendation_result_user_context_rank (user_id, context, rank)
- idx_recommendation_result_score_confidence (score, confidence_score)
- idx_recommendation_result_created (created_at)
- idx_recommendation_result_expires (expires_at)
- idx_recommendation_result_clicked_rated (was_clicked, was_rated)

---

### 5. **recommendations_demographic_cluster** (DemographicCluster Entity)

**Màu sắc**: #9013FE (Purple)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
cluster_id: VARCHAR(50) NOT NULL (unique)
name: VARCHAR(100) NOT NULL
description: TEXT NOT NULL DEFAULT ''
age_range_min: INTEGER NULL
age_range_max: INTEGER NULL
primary_gender: VARCHAR(10) NULL
common_occupations: JSONB NOT NULL DEFAULT '[]'
geographic_regions: JSONB NOT NULL DEFAULT '[]'
preferred_genres: JSONB NOT NULL DEFAULT '{}'
average_rating: FLOAT NOT NULL DEFAULT 0.0
rating_variance: FLOAT NOT NULL DEFAULT 0.0
user_count: INTEGER NOT NULL DEFAULT 0
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (cluster_id)

**Indexes:**

- idx_demographic_cluster_cluster_id (cluster_id)
- idx_demographic_cluster_age_range (age_range_min, age_range_max)
- idx_demographic_cluster_primary_gender (primary_gender)
- idx_demographic_cluster_user_count (user_count)

---

### 6. **recommendations_metrics** (RecommendationMetrics Entity)

**Màu sắc**: #9013FE (Purple)
**Kích thước**: 120x80 pixels

**Trường dữ liệu:**

```
id: SERIAL (Primary Key)
date: DATE NOT NULL
recommendation_type: VARCHAR(20) NOT NULL
total_recommendations: INTEGER NOT NULL DEFAULT 0
unique_users: INTEGER NOT NULL DEFAULT 0
unique_movies: INTEGER NOT NULL DEFAULT 0
average_predicted_rating: FLOAT NOT NULL DEFAULT 0.0
average_actual_rating: FLOAT NOT NULL DEFAULT 0.0
rmse: FLOAT NOT NULL DEFAULT 0.0
mae: FLOAT NOT NULL DEFAULT 0.0
click_through_rate: FLOAT NOT NULL DEFAULT 0.0
conversion_rate: FLOAT NOT NULL DEFAULT 0.0
average_rating_given: FLOAT NOT NULL DEFAULT 0.0
intra_list_diversity: FLOAT NOT NULL DEFAULT 0.0
novelty_score: FLOAT NOT NULL DEFAULT 0.0
catalog_coverage: FLOAT NOT NULL DEFAULT 0.0
created_at: TIMESTAMP NOT NULL DEFAULT NOW()
```

**Constraints:**

- PRIMARY KEY (id)
- UNIQUE (date, recommendation_type)

**Indexes:**

- idx_recommendation_metrics_date_type (date, recommendation_type)
- idx_recommendation_metrics_ctr (click_through_rate)
- idx_recommendation_metrics_conversion (conversion_rate)

---

## 🔗 Relationships trong Recommendations App

### One-to-One (1:1)

```
User → UserPreference (1:1)
```

### One-to-Many (1:N)

```
User → RecommendationResult (1:N)
Movie → RecommendationResult (1:N)
```

### Many-to-Many (N:N)

```
User ↔ User (through UserSimilarity)
Movie ↔ Movie (through MovieSimilarity)
```

### Foreign Key Relationships

```
UserPreference.user_id → User.id
UserSimilarity.user1_id → User.id
UserSimilarity.user2_id → User.id
MovieSimilarity.movie1_id → Movie.id
MovieSimilarity.movie2_id → Movie.id
RecommendationResult.user_id → User.id
RecommendationResult.movie_id → Movie.id
```

---

## 📝 Hướng dẫn vẽ Recommendations App trong StarUML

### Bước 1: Vẽ Core Entities

1. Tạo UserPreference, RecommendationResult, DemographicCluster, RecommendationMetrics
2. Màu sắc: #9013FE (Purple)
3. Kích thước: 140x100 cho core entities, 120x80 cho supporting entities

### Bước 2: Vẽ Junction Tables

1. Tạo UserSimilarity và MovieSimilarity
2. Màu sắc: #CCCCCC (Gray)
3. Kích thước: 120x80
4. Đánh dấu Composite Primary Keys

### Bước 3: Vẽ Relationships

1. Vẽ One-to-One relationship giữa User và UserPreference
2. Vẽ One-to-Many relationships từ User và Movie đến RecommendationResult
3. Vẽ Many-to-Many relationships qua junction tables
4. Thêm cardinality và relationship names

---

**Lưu ý**: Đây là chi tiết cho Recommendations App. Cuối cùng sẽ là Movies App (phức tạp nhất).
