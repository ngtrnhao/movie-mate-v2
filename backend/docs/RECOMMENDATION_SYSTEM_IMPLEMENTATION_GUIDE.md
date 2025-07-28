# 🎬 Movie Recommendation System Implementation Guide

## 📖 Tổng quan về Hệ thống Khuyến nghị Phim

Hệ thống khuyến nghị phim sử dụng kết hợp **Collaborative Filtering** và **Demographic Filtering** để cung cấp recommendations chính xác và cá nhân hóa cho người dùng.

### 🎯 Các Kỹ thuật Khuyến nghị được Implement:

1. **Collaborative Filtering** - Lọc cộng tác dựa trên hành vi người dùng
2. **Demographic Filtering** - Lọc nhân khẩu học dựa trên đặc điểm người dùng
3. **Content-Based Filtering** - Lọc dựa trên nội dung phim
4. **Hybrid Recommendation** - Kết hợp nhiều phương pháp

---

## 🏗️ Kiến trúc Hệ thống

### **Models Chính:**

```
apps/recommendations/models.py:
├── UserPreference          # Thông tin preference người dùng
├── UserSimilarity         # Ma trận similarity giữa users
├── MovieSimilarity        # Ma trận similarity giữa movies
├── RecommendationResult   # Kết quả recommendations
├── DemographicCluster     # Clusters nhân khẩu học
└── RecommendationMetrics  # Metrics đánh giá hiệu suất
```

### **Services Chính:**

```
apps/recommendations/services.py:
├── CollaborativeFilteringService    # Collaborative filtering algorithms
├── DemographicFilteringService      # Demographic filtering algorithms
└── HybridRecommendationService      # Hybrid recommendation engine
```

---

## 🔧 Setup và Cài đặt

### **1. Migration Database:**

```bash
# Tạo migrations cho recommendations app
python manage.py makemigrations recommendations

# Apply migrations
python manage.py migrate recommendations
```

### **2. Setup Recommendation System:**

```bash
# Setup demographic clusters và user preferences
python manage.py setup_recommendations --recalculate-clusters --update-preferences

# Dry run để xem những gì sẽ được tạo
python manage.py setup_recommendations --dry-run --recalculate-clusters --update-preferences
```

### **3. Thêm URL Routes:**

```python
# backend/config/urls.py
urlpatterns = [
    # ... existing patterns ...
    path('recommendations/', include('apps.recommendations.urls')),
]
```

---

## 📊 Collaborative Filtering Implementation

### **Thuật toán User-Based Collaborative Filtering:**

```python
from apps.recommendations.services import CollaborativeFilteringService

# Initialize service
collab_service = CollaborativeFilteringService()

# Generate recommendations for user
recommendations = collab_service.generate_collaborative_recommendations(
    user=user,
    limit=20,
    context='homepage'
)
```

### **Các phương pháp tính Similarity:**

1. **Pearson Correlation** (default):

   ```python
   similarity = collab_service.calculate_user_similarity(user1, user2, method='pearson')
   ```

2. **Cosine Similarity**:

   ```python
   similarity = collab_service.calculate_user_similarity(user1, user2, method='cosine')
   ```

3. **Jaccard Similarity**:

   ```python
   similarity = collab_service.calculate_user_similarity(user1, user2, method='jaccard')
   ```

4. **Euclidean Distance**:
   ```python
   similarity = collab_service.calculate_user_similarity(user1, user2, method='euclidean')
   ```

### **Caching và Optimization:**

- **Precomputed Similarities**: Lưu trữ similarities đã tính để tái sử dụng
- **Redis Caching**: Cache recommendations 1 giờ
- **Batch Processing**: Xử lý candidates theo batch để tối ưu performance
- **Database Indexes**: Tối ưu queries với proper indexing

---

## 👥 Demographic Filtering Implementation

### **Tạo Demographic Clusters:**

```python
from apps.recommendations.services import DemographicFilteringService

# Initialize service
demo_service = DemographicFilteringService()

# Create demographic clusters
demo_service.create_demographic_clusters(recalculate=True)
```

### **Cấu trúc Demographic Clusters:**

- **Age Groups**: Under 18, 18-24, 25-34, 35-44, 45-54, 55+
- **Gender**: Male (M), Female (F), Other (O)
- **Occupations**: Based on MovieLens dataset classifications
- **Geographic Regions**: Based on user location data

### **Genre Preferences Calculation:**

```python
# Get user's demographic cluster
cluster = demo_service.get_user_demographic_cluster(user)

# Generate demographic-based recommendations
recommendations = demo_service.generate_demographic_recommendations(
    user=user,
    limit=20,
    context='homepage'
)
```

---

## 🔄 Hybrid Recommendation System

### **Weighted Combination:**

```python
from apps.recommendations.services import HybridRecommendationService

# Initialize hybrid service
hybrid_service = HybridRecommendationService()

# Default weights
weights = {
    'collaborative': 0.4,      # 40% từ collaborative filtering
    'demographic': 0.3,        # 30% từ demographic filtering
    'content_based': 0.2,      # 20% từ content-based
    'trending': 0.1            # 10% từ trending movies
}

# Generate hybrid recommendations
recommendations = hybrid_service.generate_hybrid_recommendations(
    user=user,
    limit=20,
    context='homepage'
)
```

### **Adaptive Method Selection:**

Hệ thống tự động chọn phương pháp tốt nhất cho từng user:

- **>= 20 ratings**: Sử dụng Collaborative Filtering
- **< 10 ratings + có demographics**: Sử dụng Demographic Filtering
- **Default**: Sử dụng Hybrid approach

---

## 🌐 API Endpoints

### **REST API Usage:**

```bash
# Get collaborative filtering recommendations
GET /recommendations/api/collaborative/?limit=20&context=homepage

# Get demographic filtering recommendations
GET /recommendations/api/demographic/?limit=20&context=homepage

# Get hybrid recommendations
GET /recommendations/api/hybrid/?limit=20&context=homepage

# Get personalized recommendations (auto-selects best method)
GET /recommendations/api/personalized/?limit=20&context=homepage

# Submit feedback on recommendations
POST /recommendations/api/feedback/
{
    "movie_id": 123,
    "recommendation_type": "collaborative",
    "context": "homepage",
    "feedback_type": "like",
    "action": "clicked"
}

# Get user recommendation profile
GET /recommendations/api/profile/
```

### **Response Format:**

```json
{
    "status": "success",
    "data": {
        "movies": [...],
        "recommendation_type": "hybrid",
        "context": "homepage",
        "count": 20,
        "weights": {...},
        "cached": false
    }
}
```

---

## 📈 Performance Optimization

### **Caching Strategy:**

```python
# User similarity cache (1 hour)
cache_key = f"similar_users:{user.id}:{method}:{limit}"

# Recommendations cache (1 hour)
cache_key = f"collaborative_recs:{user.id}:{context}:{limit}"

# Precomputed similarities
UserSimilarity.objects.filter(similarity_type='collaborative')
```

### **Database Optimization:**

```sql
-- User similarity lookup
CREATE INDEX idx_user_similarity_lookup ON recommendations_user_similarity(user1_id, similarity_type, similarity_score);

-- Recommendation results
CREATE INDEX idx_recommendation_user_type ON recommendations_result(user_id, recommendation_type, rank);

-- User preferences
CREATE INDEX idx_user_preferences_cluster ON recommendations_user_preference(demographic_cluster);
```

### **Background Tasks:**

```python
# Celery tasks cho background processing
@shared_task
def update_user_similarities():
    """Update user similarity matrix"""

@shared_task
def recalculate_demographic_clusters():
    """Recalculate demographic clusters"""

@shared_task
def generate_recommendations_for_active_users():
    """Pre-generate recommendations for active users"""
```

---

## 📊 Monitoring và Analytics

### **Recommendation Metrics:**

```python
from apps.recommendations.models import RecommendationMetrics

# Track metrics daily
metrics = RecommendationMetrics.objects.create(
    date=today,
    recommendation_type='collaborative',
    total_recommendations=1000,
    unique_users=250,
    click_through_rate=0.15,
    conversion_rate=0.08,
    rmse=0.85
)
```

### **Admin Interface:**

- **User Preferences Management**: Xem và chỉnh sửa user preferences
- **Demographic Clusters**: Quản lý và monitor clusters
- **Recommendation Results**: Track recommendations và feedback
- **Performance Metrics**: Monitor system performance

---

## 🚀 Frontend Integration

### **React Components Integration:**

```javascript
// Get personalized recommendations
const getPersonalizedRecommendations = async (
  limit = 20,
  context = "homepage"
) => {
  const response = await fetch(
    `/recommendations/api/personalized/?limit=${limit}&context=${context}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  const data = await response.json();
  return data.data.movies;
};

// Submit recommendation feedback
const submitRecommendationFeedback = async (
  movieId,
  recommendationType,
  feedbackType
) => {
  await fetch("/recommendations/api/feedback/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      movie_id: movieId,
      recommendation_type: recommendationType,
      feedback_type: feedbackType,
      action: "clicked",
    }),
  });
};
```

### **Recommendation Contexts:**

- `homepage`: Trang chủ recommendations
- `after_rating`: Sau khi user rate phim
- `profile`: Trang profile của user
- `genre_explorer`: Trong genre explorer
- `similar_movies`: Trang chi tiết phim
- `onboarding`: Quá trình onboarding user mới

---

## 🧪 Testing và Validation

### **Unit Tests:**

```python
from django.test import TestCase
from apps.recommendations.services import CollaborativeFilteringService

class CollaborativeFilteringTestCase(TestCase):
    def test_user_similarity_calculation(self):
        # Test similarity calculation
        similarity = self.collab_service.calculate_user_similarity(
            self.user1, self.user2, method='pearson'
        )
        self.assertGreaterEqual(similarity, -1.0)
        self.assertLessEqual(similarity, 1.0)

    def test_recommendation_generation(self):
        # Test recommendation generation
        recommendations = self.collab_service.generate_collaborative_recommendations(
            self.user, limit=10
        )
        self.assertLessEqual(len(recommendations), 10)
```

### **Performance Tests:**

```python
def test_recommendation_performance(self):
    """Test recommendation generation performance"""
    start_time = time.time()

    recommendations = self.hybrid_service.generate_hybrid_recommendations(
        self.user, limit=20
    )

    end_time = time.time()
    execution_time = end_time - start_time

    # Should complete within 2 seconds
    self.assertLess(execution_time, 2.0)
```

---

## 🔧 Maintenance và Updates

### **Regular Maintenance Tasks:**

```bash
# Daily: Update user preferences
python manage.py setup_recommendations --update-preferences --batch-size=500

# Weekly: Recalculate demographic clusters
python manage.py setup_recommendations --recalculate-clusters

# Monthly: Update similarity matrices
python manage.py calculate_user_similarities --batch-size=100
```

### **Performance Monitoring:**

```python
# Monitor recommendation performance
GET /recommendations/api/stats/

# Response:
{
    "total_users_with_preferences": 1250,
    "total_demographic_clusters": 18,
    "recommendations_generated_last_7_days": 15000,
    "active_recommendation_types": 4,
    "system_status": "active"
}
```

---

## 📝 Best Practices

### **1. Data Quality:**

- Đảm bảo user có đủ demographic data
- Clean và validate rating data
- Monitor data consistency

### **2. Algorithm Tuning:**

- Adjust similarity thresholds dựa trên data size
- Fine-tune hybrid weights based on performance metrics
- Regular A/B testing để optimize

### **3. Scalability:**

- Use precomputed similarities cho large user bases
- Implement efficient caching strategies
- Consider matrix factorization cho very large datasets

### **4. User Experience:**

- Provide explanations cho recommendations
- Allow user feedback để improve algorithms
- Handle cold start problem cho new users

---

## 🎯 Kết luận

Hệ thống khuyến nghị phim đã được implement hoàn chỉnh với:

✅ **Collaborative Filtering** với multiple similarity methods
✅ **Demographic Filtering** với automatic clustering
✅ **Hybrid Recommendation** kết hợp multiple approaches
✅ **Performance Optimization** với caching và indexing
✅ **Complete API** cho frontend integration
✅ **Admin Interface** để management và monitoring
✅ **Feedback System** để continuous improvement

Hệ thống này cung cấp recommendations chính xác, scalable và có thể maintain dễ dàng cho movie recommendation platform.
