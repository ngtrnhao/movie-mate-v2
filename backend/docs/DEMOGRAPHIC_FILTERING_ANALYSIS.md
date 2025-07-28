# 📊 Báo Cáo Phân Tích Hệ Khuyến Nghị Demographic Filtering

## 🔍 1. TÌNH TRẠNG DATABASE HIỆN TẠI

### ✅ Dữ liệu Demographic Có Sẵn:

**User Model (apps/users/models.py):**

```python
class User(AbstractUser):
    # Thông tin demographic cơ bản
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    location = models.CharField(max_length=255, blank=True, null=True)

    # Thông tin từ MovieLens dataset
    age_group = models.CharField(max_length=20, blank=True, null=True)
    occupation = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)

    # Loại thành viên
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='member')
```

**Đánh giá:**

- ✅ **HOÀN CHỈNH**: Có đầy đủ các trường demographic cần thiết
- ✅ **INDEXED**: Đã có indexes cho age_group, occupation, zip_code
- ✅ **CHUẨN HÓA**: Follow MovieLens standard

### ✅ Models Hỗ Trợ Demographic Filtering:

**1. DemographicCluster Model:**

```python
class DemographicCluster(models.Model):
    cluster_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    age_range_min = models.IntegerField(null=True, blank=True)
    age_range_max = models.IntegerField(null=True, blank=True)
    primary_gender = models.CharField(max_length=10, null=True, blank=True)
    common_occupations = models.JSONField(default=list, blank=True)
    preferred_genres = models.JSONField(default=dict, blank=True)
    user_count = models.IntegerField(default=0)
```

**2. UserPreference Model:**

```python
class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    demographic_cluster = models.CharField(max_length=50, null=True, blank=True)
    behavior_cluster = models.CharField(max_length=50, null=True, blank=True)
    # Vector preferences
    genre_preferences = models.JSONField(default=dict, blank=True)
    actor_preferences = models.JSONField(default=dict, blank=True)
    director_preferences = models.JSONField(default=dict, blank=True)
```

**3. UserSimilarity Model:**

```python
class UserSimilarity(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='similarity_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='similarity_as_user2')
    similarity_type = models.CharField(max_length=20, choices=[
        ('collaborative', 'Collaborative Filtering'),
        ('demographic', 'Demographic Similarity'),  # ✅ Hỗ trợ demographic
        ('behavioral', 'Behavioral Similarity'),
        ('hybrid', 'Hybrid Similarity'),
    ])
    similarity_score = models.FloatField()
```

## 🔧 2. IMPLEMENTATION HIỆN TẠI

### ✅ DemographicFilteringService (apps/recommendations/services.py):

**Tính năng đã implement:**

1. **Tạo Demographic Clusters:**

```python
def create_demographic_clusters(self, recalculate=False):
    # Tạo clusters dựa trên age_group + gender
    # Tính toán genre preferences cho mỗi cluster
    # Lưu cluster characteristics
```

2. **Tìm Cluster cho User:**

```python
def get_user_demographic_cluster(self, user):
    # Map user vào cluster phù hợp
    # Dựa trên age, gender, occupation
```

3. **Generate Recommendations:**

```python
def generate_demographic_recommendations(self, user, limit=20):
    # Tìm cluster của user
    # Lấy movies được cluster đánh giá cao
    # Tính toán demographic score
    # Kết hợp với cluster preferences
```

### ✅ ML Algorithm Support (apps/recommendations/ml_algorithms.py):

**DemographicRecommender Class:**

```python
class DemographicRecommender:
    def __init__(self, users_df, cluster_data):
        self.users_df = users_df
        self.cluster_labels = cluster_data.get('cluster_labels', [])
        self.user_clusters = {}

    def get_similar_users(self, user_id, n_similar=50):
        # Tìm users trong cùng cluster

    def recommend_for_user(self, user_id, ratings_df, n_recommendations=10):
        # Lấy movies phổ biến trong cluster
```

### ✅ Data Preprocessing (apps/recommendations/preprocessing.py):

**Demographic Data Processing:**

```python
def prepare_demographic_data(self) -> Dict[str, Any]:
    # Encode categorical variables (gender, occupation, age_group)
    # Scale numerical features (age)
    # Create demographic clusters using KMeans
    # Calculate cluster statistics
```

## 🎯 3. QUÁ TRÌNH XÂY DỰNG HỆ KHUYẾN NGHỊ DEMOGRAPHIC

### Bước 1: Vector Hóa Dữ Liệu Người Dùng

#### A. Categorical Encoding:

```python
def _encode_demographics(self, users_df: pd.DataFrame) -> pd.DataFrame:
    """Vector hóa các biến categorical"""
    encoded_df = users_df.copy()

    # Label encode categorical variables
    categorical_columns = ['gender', 'occupation', 'age_group']

    for col in categorical_columns:
        if col in encoded_df.columns:
            le = LabelEncoder()
            encoded_df[f'{col}_encoded'] = le.fit_transform(encoded_df[col].astype(str))
            self.encoders[f'{col}_encoder'] = le
```

**Quá trình:**

1. **Gender Encoding**: M=0, F=1, O=2
2. **Occupation Encoding**: Mã hóa nghề nghiệp thành số
3. **Age Group Encoding**: Mã hóa nhóm tuổi thành số
4. **Location Encoding**: Mã hóa vị trí địa lý

#### B. Numerical Scaling:

```python
def _scale_demographic_features(self, demographics_df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa dữ liệu số"""
    numerical_cols = ['age']
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(demographics_df[numerical_cols].fillna(0))
```

### Bước 2: Xây Dựng Ma Trận Tương Đồng Người Dùng

#### A. Demographic Clustering:

```python
def _create_demographic_clusters(self, demographics_df: pd.DataFrame) -> Dict:
    """Tạo clusters demographic bằng KMeans"""

    # Chọn features cho clustering
    cluster_features = ['age', 'gender_encoded', 'occupation_encoded']
    X = demographics_df[cluster_features].fillna(0)

    # Chuẩn hóa dữ liệu
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # KMeans clustering
    n_clusters = min(8, len(X) // 10)  # Adaptive số clusters
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(X_scaled)
```

#### B. Similarity Calculation:

```python
def calculate_demographic_similarity(self, user1, user2) -> float:
    """Tính tương đồng demographic giữa 2 users"""

    # Weighted features
    weights = {
        'age_similarity': 0.3,
        'gender_similarity': 0.4,
        'occupation_similarity': 0.2,
        'location_similarity': 0.1
    }

    total_similarity = 0.0

    # Age similarity (normalized by age difference)
    if user1.age and user2.age:
        age_diff = abs(user1.age - user2.age)
        age_similarity = max(0, 1 - (age_diff / 50))  # Normalize by max age diff
        total_similarity += weights['age_similarity'] * age_similarity

    # Gender similarity (exact match)
    gender_similarity = 1.0 if user1.gender == user2.gender else 0.0
    total_similarity += weights['gender_similarity'] * gender_similarity

    # Occupation similarity
    occupation_similarity = 1.0 if user1.occupation == user2.occupation else 0.0
    total_similarity += weights['occupation_similarity'] * occupation_similarity

    return total_similarity
```

### Bước 3: Ma Trận User-User Similarity

```python
def build_demographic_similarity_matrix(self, users) -> np.ndarray:
    """Xây dựng ma trận tương đồng demographic"""

    n_users = len(users)
    similarity_matrix = np.zeros((n_users, n_users))

    for i in range(n_users):
        for j in range(i+1, n_users):
            similarity = self.calculate_demographic_similarity(users[i], users[j])
            similarity_matrix[i][j] = similarity
            similarity_matrix[j][i] = similarity  # Symmetric matrix

    return similarity_matrix
```

### Bước 4: Generate Recommendations

```python
def generate_demographic_recommendations(self, target_user, similarity_matrix, user_ratings):
    """Tạo recommendations dựa trên demographic similarity"""

    # 1. Tìm similar users
    user_index = self.get_user_index(target_user)
    similarities = similarity_matrix[user_index]

    # 2. Lấy top K similar users
    top_similar_indices = np.argsort(similarities)[::-1][:50]

    # 3. Aggregate ratings từ similar users
    candidate_movies = {}

    for similar_user_idx in top_similar_indices:
        similarity_score = similarities[similar_user_idx]

        if similarity_score > 0.1:  # Threshold
            similar_user_ratings = user_ratings[similar_user_idx]

            for movie_id, rating in similar_user_ratings.items():
                if movie_id not in target_user_ratings:  # Chưa xem
                    if movie_id not in candidate_movies:
                        candidate_movies[movie_id] = []

                    weighted_rating = rating * similarity_score
                    candidate_movies[movie_id].append(weighted_rating)

    # 4. Calculate final scores
    final_scores = {}
    for movie_id, weighted_ratings in candidate_movies.items():
        final_scores[movie_id] = np.mean(weighted_ratings)

    # 5. Sort and return top recommendations
    sorted_movies = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    return [movie_id for movie_id, score in sorted_movies[:20]]
```

## 🚀 4. NHỮNG GÌ CẦN IMPLEMENT/HOÀN THIỆN

### ❌ Thiếu sót chính:

1. **Advanced Similarity Metrics:**

   - Chỉ có basic age + gender clustering
   - Thiếu cosine similarity, euclidean distance cho demographic vectors
   - Thiếu weighted similarity dựa trên importance của từng feature

2. **Feature Engineering:**

   - Chưa combine multiple demographic features thành composite vectors
   - Chưa handle missing data một cách sophisticated
   - Thiếu demographic profile embeddings

3. **Cold Start Problem:**

   - Chưa có strategy cho users mới không có demographic data
   - Chưa có fallback mechanism

4. **Performance Optimization:**
   - Chưa cache similarity matrices
   - Chưa implement batch processing cho large datasets

### ✅ Implementation Plan:

#### Phase 1: Enhanced Demographic Vectorization

```python
class AdvancedDemographicVectorizer:
    """Advanced demographic feature engineering"""

    def __init__(self):
        self.age_bins = [(0, 18), (18, 25), (25, 35), (35, 45), (45, 55), (55, 100)]
        self.occupation_groups = {
            'technical': ['engineer', 'programmer', 'scientist'],
            'creative': ['artist', 'writer', 'designer'],
            'business': ['manager', 'executive', 'sales'],
            # ...
        }

    def create_demographic_vector(self, user) -> np.ndarray:
        """Tạo vector demographic comprehensive"""

        features = []

        # Age features (one-hot encoded bins)
        age_vector = self._encode_age_bins(user.age)
        features.extend(age_vector)

        # Gender features (one-hot)
        gender_vector = self._encode_gender(user.gender)
        features.extend(gender_vector)

        # Occupation group features
        occupation_vector = self._encode_occupation_groups(user.occupation)
        features.extend(occupation_vector)

        # Geographic features
        location_vector = self._encode_location(user.location, user.zip_code)
        features.extend(location_vector)

        # User type features
        user_type_vector = self._encode_user_type(user.user_type)
        features.extend(user_type_vector)

        return np.array(features)

    def _encode_age_bins(self, age) -> List[float]:
        """Encode age into bins"""
        if not age:
            return [0.0] * len(self.age_bins)

        age_vector = []
        for min_age, max_age in self.age_bins:
            if min_age <= age < max_age:
                age_vector.append(1.0)
            else:
                age_vector.append(0.0)
        return age_vector
```

#### Phase 2: Advanced Similarity Calculation

```python
class DemographicSimilarityCalculator:
    """Advanced demographic similarity calculation"""

    def __init__(self, vectorizer: AdvancedDemographicVectorizer):
        self.vectorizer = vectorizer
        self.feature_weights = {
            'age': 0.25,
            'gender': 0.30,
            'occupation': 0.25,
            'location': 0.10,
            'user_type': 0.10
        }

    def calculate_cosine_similarity(self, user1_vector, user2_vector) -> float:
        """Cosine similarity giữa demographic vectors"""
        return cosine_similarity([user1_vector], [user2_vector])[0][0]

    def calculate_weighted_similarity(self, user1, user2) -> float:
        """Weighted similarity với different importance cho features"""

        total_similarity = 0.0
        total_weight = 0.0

        # Age similarity với Gaussian kernel
        if user1.age and user2.age:
            age_diff = abs(user1.age - user2.age)
            age_similarity = np.exp(-(age_diff ** 2) / (2 * 10 ** 2))  # sigma=10
            total_similarity += self.feature_weights['age'] * age_similarity
            total_weight += self.feature_weights['age']

        # Gender exact match
        if user1.gender and user2.gender:
            gender_similarity = 1.0 if user1.gender == user2.gender else 0.0
            total_similarity += self.feature_weights['gender'] * gender_similarity
            total_weight += self.feature_weights['gender']

        # Occupation group similarity
        if user1.occupation and user2.occupation:
            occupation_similarity = self._calculate_occupation_similarity(
                user1.occupation, user2.occupation
            )
            total_similarity += self.feature_weights['occupation'] * occupation_similarity
            total_weight += self.feature_weights['occupation']

        return total_similarity / total_weight if total_weight > 0 else 0.0
```

#### Phase 3: Matrix Optimization

```python
class OptimizedDemographicMatrix:
    """Optimized similarity matrix với caching và batch processing"""

    def __init__(self):
        self.cache_timeout = 3600 * 24  # 24 hours
        self.batch_size = 1000

    def build_similarity_matrix_batch(self, users) -> csr_matrix:
        """Build sparse similarity matrix với batch processing"""

        n_users = len(users)
        similarities = []

        # Process in batches
        for i in range(0, n_users, self.batch_size):
            batch_end = min(i + self.batch_size, n_users)
            batch_similarities = self._process_batch(users[i:batch_end], users)
            similarities.extend(batch_similarities)

        # Convert to sparse matrix
        return self._create_sparse_matrix(similarities, n_users)

    def _process_batch(self, batch_users, all_users) -> List[Tuple]:
        """Process một batch users"""
        similarities = []

        for i, user1 in enumerate(batch_users):
            for j, user2 in enumerate(all_users):
                if i != j:
                    similarity = self.calculate_similarity(user1, user2)
                    if similarity > 0.1:  # Chỉ store non-zero similarities
                        similarities.append((i, j, similarity))

        return similarities
```

## 📊 5. ĐÁNH GIÁ VÀ METRICS

### Performance Metrics cần track:

1. **Coverage**: % users có thể nhận recommendations
2. **Diversity**: Đa dạng trong recommendations
3. **Novelty**: Tính mới lạ của recommendations
4. **Accuracy**: Độ chính xác predictions
5. **Scalability**: Performance với large datasets

### Implementation Metrics Class:

```python
class DemographicFilteringMetrics:
    """Metrics cho demographic filtering"""

    def calculate_coverage(self, users, recommendations) -> float:
        """Coverage = users nhận được recs / total users"""
        users_with_recs = len([u for u in users if recommendations.get(u.id)])
        return users_with_recs / len(users)

    def calculate_diversity(self, recommendations) -> float:
        """Intra-list diversity của recommendations"""
        # Calculate average pairwise distance trong recommendation lists
        pass

    def calculate_demographic_accuracy(self, test_data) -> Dict:
        """Accuracy cho mỗi demographic group"""
        accuracy_by_group = {}

        for age_group in ['18-24', '25-34', '35-44', '45-54', '55+']:
            group_users = test_data[test_data['age_group'] == age_group]
            group_accuracy = self._calculate_rmse(group_users)
            accuracy_by_group[age_group] = group_accuracy

        return accuracy_by_group
```

## ✅ 6. KẾT LUẬN VÀ KHUYẾN NGHỊ

### Tình trạng hiện tại:

- ✅ **Database schema**: HOÀN CHỈNH
- ✅ **Basic implementation**: CÓ SẴN
- ⚠️ **Advanced features**: CẦN HOÀN THIỆN
- ❌ **Optimization**: CHƯA CÓ

### Priorities để hoàn thiện:

1. **High Priority:**

   - Implement advanced similarity metrics (cosine, weighted)
   - Add comprehensive feature engineering
   - Optimize performance với caching

2. **Medium Priority:**

   - Add cold start handling
   - Implement cross-validation metrics
   - Add demographic bias detection

3. **Low Priority:**
   - Advanced clustering algorithms (DBSCAN, hierarchical)
   - Deep learning embeddings cho demographics
   - Real-time similarity updates

### Next Steps:

1. Implement `AdvancedDemographicVectorizer`
2. Enhance similarity calculation methods
3. Add comprehensive testing và metrics
4. Optimize cho production performance

**Hệ thống hiện tại đã có foundation tốt, chỉ cần enhance và optimize để ready cho production!**
