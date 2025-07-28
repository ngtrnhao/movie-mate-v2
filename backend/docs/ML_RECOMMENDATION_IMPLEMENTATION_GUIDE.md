# 🤖 ML-Based Movie Recommendation System Implementation Guide

## 📖 Tổng quan về Hệ thống ML Recommendation

Hệ thống khuyến nghị phim sử dụng **Machine Learning** tiên tiến với các thư viện **Surprise**, **scikit-learn**, và **TensorFlow** để cung cấp recommendations chính xác và cá nhân hóa.

### 🎯 Các Kỹ thuật ML được Implement:

1. **Collaborative Filtering (Surprise)** - SVD, NMF, KNN algorithms
2. **Content-Based Filtering (scikit-learn)** - TF-IDF, Cosine Similarity
3. **Demographic Filtering (scikit-learn)** - KMeans Clustering
4. **Deep Learning (TensorFlow)** - Neural Collaborative Filtering
5. **Hybrid Models** - Ensemble of multiple approaches

---

## 🔧 Cài đặt và Dependencies

### **1. Cài đặt ML Libraries:**

```bash
# Cài đặt tất cả ML dependencies
pip install -r backend/requirements/ml_requirements.txt

# Hoặc cài đặt từng thư viện
pip install scikit-surprise==1.1.4
pip install scikit-learn==1.3.2
pip install tensorflow==2.15.0
pip install pandas==2.1.4
pip install numpy==1.25.2
pip install scipy==1.11.4

# Text processing (cho content-based filtering)
pip install nltk==3.8.1
pip install spacy==3.7.2
pip install gensim==4.3.2

# Optional: Performance optimization
pip install numba==0.58.1
pip install joblib==1.3.2
```

### **2. Setup NLTK Data (cho text processing):**

```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
```

### **3. Kiểm tra TensorFlow GPU (optional):**

```bash
python -c "import tensorflow as tf; print('GPU Available:', tf.config.list_physical_devices('GPU'))"
```

---

## 📊 Phân tích Dữ liệu và Đánh giá ML Readiness

### **Bước 1: Chạy Dataset Analysis**

```bash
# Phân tích dataset hiện tại
python manage.py analyze_dataset --verbose --format both

# Output sẽ bao gồm:
# - Dataset overview (users, movies, ratings)
# - Matrix sparsity analysis
# - ML algorithm readiness assessment
# - Preprocessing requirements
# - Library recommendations
```

### **Kết quả mẫu:**

```
🔍 KEY FINDINGS
==================================================

📊 Dataset Overview:
  • Total Users: 1,234
  • Total Movies: 5,678
  • Total Ratings: 12,345
  • Matrix Sparsity: 99.82%
  • Matrix Density: 0.18%

🤖 ML Algorithm Readiness:
  • Collaborative Filtering: ✅ Ready
  • Demographic Filtering: ❌ Not Ready
  • Content Based Filtering: ✅ Ready
  • Deep Learning: ❌ Not Ready
  • Hybrid Approaches: ✅ Ready

💡 RECOMMENDATIONS
==================================================

🔧 Preprocessing Steps Needed:
  1. Matrix factorization/dimensionality reduction needed due to high sparsity
  2. Text preprocessing needed for movie overviews (TF-IDF, word2vec)
  3. Genre encoding and feature engineering needed
  4. Feature scaling and normalization for numerical features

📚 Recommended Libraries:
  🔴 High Priority:
    • Surprise: Specialized for collaborative filtering with rating matrices
    • scikit-learn: Essential for preprocessing and traditional ML algorithms
    • pandas: Essential for data preprocessing and analysis
```

---

## 🔄 Data Preprocessing Pipeline

### **Bước 2: Chạy Data Preprocessing**

```bash
# Preprocessing toàn bộ dữ liệu cho tất cả ML algorithms
python manage.py train_ml_models --preprocess-only

# Hoặc với custom parameters
python manage.py train_ml_models \
    --preprocess-only \
    --test-size 0.2 \
    --random-state 42 \
    --output-dir /path/to/output
```

### **Preprocessing bao gồm:**

1. **Collaborative Filtering Data:**

   - Tạo user-item rating matrix
   - Format data cho Surprise library
   - Sparse matrix optimization

2. **Content-Based Data:**

   - TF-IDF vectorization của movie descriptions
   - Genre encoding và feature engineering
   - Cosine similarity matrix calculation

3. **Demographic Data:**

   - Categorical encoding (gender, occupation, age_group)
   - KMeans clustering cho demographic groups
   - Feature scaling và normalization

4. **Deep Learning Data:**
   - User/Movie embedding preparation
   - Training sequences creation
   - Train/test split cho neural networks

---

## 🤖 ML Model Training

### **Bước 3: Train ML Models**

```bash
# Train tất cả models
python manage.py train_ml_models

# Train specific algorithms
python manage.py train_ml_models \
    --algorithms collaborative content_based demographic

# Enable hyperparameter tuning (chậm hơn nhưng tốt hơn)
python manage.py train_ml_models \
    --hyperparameter-tuning \
    --algorithms collaborative deep_learning

# Train only (skip preprocessing)
python manage.py train_ml_models --train-only
```

### **Kết quả Training mẫu:**

```
🤖 STEP 2: ML MODEL TRAINING
============================================================

🔹 Collaborative Filtering Results:
  ✅ Best Model: SVD
    • SVD: RMSE=0.8745, MAE=0.6892
    • NMF: RMSE=0.9123, MAE=0.7234
    • KNNBasic: RMSE=0.9567, MAE=0.7456

🔹 Content Based Filtering Results:
  ✅ Similarity Matrix: (5678, 5678)
  📊 Evaluation Score: 4.2341

🔹 Demographic Filtering Results:
  ✅ Demographic Clusters: 8

🔹 Deep Learning Results:
  ✅ Neural CF: RMSE=0.8234, MAE=0.6543
```

---

## 🏗️ Architecture và Components

### **Kiến trúc ML System:**

```
apps/recommendations/
├── data_analysis.py          # Dataset analysis và ML readiness assessment
├── preprocessing.py          # Data preprocessing pipeline
├── ml_algorithms.py          # ML algorithms implementation
├── services.py               # Integration với Django services
├── models.py                 # Django models cho recommendations
├── views.py                  # API endpoints
├── management/commands/
│   ├── analyze_dataset.py    # Dataset analysis command
│   ├── train_ml_models.py    # ML training command
│   └── setup_recommendations.py  # Setup command
└── admin.py                  # Admin interface
```

### **ML Algorithms Details:**

#### **1. Collaborative Filtering (Surprise)**

```python
# Available algorithms
algorithms = {
    'SVD': SVD(n_factors=100, reg_all=0.05),
    'NMF': NMF(n_factors=50, reg_pu=0.1),
    'KNNBasic': KNNBasic(k=40, sim_options={'name': 'cosine'}),
    'KNNWithMeans': KNNWithMeans(k=40),
    'CoClustering': CoClustering(n_cltr_u=3, n_cltr_i=3)
}

# Hyperparameter tuning với GridSearchCV
param_grid = {
    'n_factors': [50, 100, 150],
    'reg_all': [0.02, 0.05, 0.1],
    'lr_all': [0.005, 0.01, 0.02]
}
```

#### **2. Content-Based Filtering (scikit-learn)**

```python
# Text features processing
tfidf = TfidfVectorizer(
    max_features=1000,
    stop_words='english',
    ngram_range=(1, 2)
)

# Similarity calculation
content_similarity = cosine_similarity(movie_features)

# Dimensionality reduction
svd = TruncatedSVD(n_components=100)
reduced_features = svd.fit_transform(tfidf_matrix)
```

#### **3. Demographic Filtering (scikit-learn)**

```python
# Demographic clustering
kmeans = KMeans(n_clusters=8, random_state=42)
cluster_labels = kmeans.fit_predict(demographic_features)

# Feature encoding
le = LabelEncoder()
encoded_gender = le.fit_transform(user_data['gender'])
```

#### **4. Deep Learning (TensorFlow)**

```python
# Neural Collaborative Filtering model
def build_ncf_model(num_users, num_movies, embedding_size=50):
    user_input = keras.Input(shape=(), name='user_id')
    movie_input = keras.Input(shape=(), name='movie_id')

    user_embedding = layers.Embedding(num_users, embedding_size)(user_input)
    movie_embedding = layers.Embedding(num_movies, embedding_size)(movie_input)

    user_vec = layers.Flatten()(user_embedding)
    movie_vec = layers.Flatten()(movie_embedding)

    concat = layers.Concatenate()([user_vec, movie_vec])
    dense1 = layers.Dense(128, activation='relu')(concat)
    dropout1 = layers.Dropout(0.2)(dense1)
    dense2 = layers.Dense(64, activation='relu')(dropout1)

    output = layers.Dense(1, activation='linear')(dense2)

    model = keras.Model(inputs=[user_input, movie_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    return model
```

---

## 🔗 Tích hợp với Django Services

### **Cập nhật Existing Services:**

```python
# apps/recommendations/services.py

class EnhancedCollaborativeFilteringService(CollaborativeFilteringService):
    """
    Enhanced CF service using trained ML models
    """

    def __init__(self):
        super().__init__()
        self.ml_engine = MLRecommendationEngine()
        self.ml_engine.load_models()  # Load trained models

    def generate_collaborative_recommendations(self, user: User, limit=20, context='homepage'):
        """
        Generate recommendations using trained ML models
        """
        try:
            # Use trained Surprise model
            if 'cf_svd' in self.ml_engine.trained_models:
                return self._get_ml_recommendations(user, limit, 'collaborative_filtering')
            else:
                # Fallback to original implementation
                return super().generate_collaborative_recommendations(user, limit, context)

        except Exception as e:
            logger.error(f"ML recommendation failed: {str(e)}")
            # Fallback to original implementation
            return super().generate_collaborative_recommendations(user, limit, context)

    def _get_ml_recommendations(self, user, limit, method):
        """Get recommendations from trained ML models"""
        return self.ml_engine.get_recommendations(user.id, method, limit)
```

### **API Integration:**

```python
# apps/recommendations/views.py

@action(detail=False, methods=['get'])
def ml_collaborative(self, request):
    """
    Get ML-based collaborative filtering recommendations
    """
    user = request.user
    limit = int(request.query_params.get('limit', 20))

    # Load ML engine
    ml_engine = MLRecommendationEngine()
    ml_engine.load_models()

    # Get recommendations
    movie_ids = ml_engine.get_recommendations(
        user.id,
        method='collaborative_filtering',
        n_recommendations=limit
    )

    # Serialize movies
    movies = Movie.objects.filter(id__in=movie_ids)
    serializer = OptimizedMovieListSerializer(movies, many=True)

    return Response({
        'status': 'success',
        'data': {
            'movies': serializer.data,
            'recommendation_type': 'ml_collaborative',
            'model_used': 'SVD',
            'count': len(movies)
        }
    })
```

---

## 📈 Model Evaluation và Monitoring

### **Evaluation Metrics:**

1. **Collaborative Filtering:**

   - RMSE (Root Mean Square Error)
   - MAE (Mean Absolute Error)
   - Precision@K, Recall@K

2. **Content-Based:**

   - Cosine similarity scores
   - Diversity metrics
   - Coverage metrics

3. **Deep Learning:**
   - Training/Validation loss
   - RMSE, MAE
   - Convergence metrics

### **Model Performance Tracking:**

```python
# Track model performance
class ModelPerformanceTracker:
    def track_recommendation_performance(self, user_id, recommendations, actual_ratings):
        # Calculate metrics
        rmse = calculate_rmse(recommendations, actual_ratings)
        mae = calculate_mae(recommendations, actual_ratings)

        # Store in database
        RecommendationMetrics.objects.create(
            date=timezone.now().date(),
            recommendation_type='ml_collaborative',
            rmse=rmse,
            mae=mae,
            total_recommendations=len(recommendations)
        )
```

---

## 🚀 Production Deployment

### **Performance Optimization:**

1. **Model Caching:**

```python
# Cache trained models
@cached_property
def trained_models(self):
    if not hasattr(self, '_trained_models'):
        self._trained_models = self.load_models()
    return self._trained_models
```

2. **Batch Prediction:**

```python
# Batch recommendations for multiple users
def batch_generate_recommendations(self, user_ids, limit=20):
    recommendations = {}
    for user_id in user_ids:
        recommendations[user_id] = self.get_recommendations(user_id, limit=limit)
    return recommendations
```

3. **Async Processing:**

```python
# Celery task for model training
@shared_task
def retrain_ml_models():
    ml_engine = MLRecommendationEngine()
    preprocessor = DataPreprocessor()

    data = preprocessor.prepare_all_data()
    results = ml_engine.train_all_models(data)

    return results
```

### **Monitoring và Alerts:**

```python
# Model performance monitoring
@shared_task
def monitor_model_performance():
    recent_metrics = RecommendationMetrics.objects.filter(
        date__gte=timezone.now() - timedelta(days=7)
    )

    avg_rmse = recent_metrics.aggregate(avg_rmse=Avg('rmse'))['avg_rmse']

    if avg_rmse > 1.0:  # Threshold
        # Send alert
        send_alert(f"Model performance degraded: RMSE={avg_rmse}")
```

---

## 📋 Quy trình Triển khai Production

### **Bước 1: Setup Environment**

```bash
# 1. Install dependencies
pip install -r backend/requirements/ml_requirements.txt

# 2. Migrate database
python manage.py migrate

# 3. Setup recommendation models
python manage.py setup_recommendations --recalculate-clusters
```

### **Bước 2: Data Analysis và Preprocessing**

```bash
# 1. Analyze current dataset
python manage.py analyze_dataset --verbose

# 2. Preprocess data for ML
python manage.py train_ml_models --preprocess-only
```

### **Bước 3: Train Models**

```bash
# 1. Train với basic algorithms
python manage.py train_ml_models --algorithms collaborative content_based

# 2. Train với hyperparameter tuning (production)
python manage.py train_ml_models \
    --hyperparameter-tuning \
    --algorithms collaborative content_based demographic
```

### **Bước 4: Integration Testing**

```bash
# Test recommendations API
curl -X GET "http://localhost:8000/recommendations/api/ml_collaborative/?limit=10" \
     -H "Authorization: Bearer <token>"
```

### **Bước 5: Monitoring Setup**

```python
# Setup periodic model retraining
CELERY_BEAT_SCHEDULE = {
    'retrain-ml-models': {
        'task': 'apps.recommendations.tasks.retrain_ml_models',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Weekly
    },
    'monitor-model-performance': {
        'task': 'apps.recommendations.tasks.monitor_model_performance',
        'schedule': crontab(minute=0),  # Hourly
    },
}
```

---

## 🎯 Best Practices

### **1. Data Quality:**

- Đảm bảo rating data đủ dense (>1% density)
- Regular data validation và cleaning
- Monitor data drift

### **2. Model Selection:**

- A/B test different algorithms
- Use ensemble methods cho production
- Regular model evaluation

### **3. Scalability:**

- Use batch processing cho large datasets
- Implement model versioning
- Cache predictions cho popular items

### **4. Monitoring:**

- Track recommendation quality metrics
- Monitor model performance degradation
- Set up alerts cho anomalies

---

## 🔧 Troubleshooting

### **Common Issues:**

1. **Memory Issues:**

```bash
# Reduce batch size
python manage.py train_ml_models --algorithms collaborative --test-size 0.1
```

2. **Sparse Matrix Warning:**

```bash
# Use matrix factorization
python manage.py analyze_dataset --verbose
# Check sparsity recommendations
```

3. **TensorFlow Issues:**

```bash
# Check GPU availability
python -c "import tensorflow as tf; print(tf.config.list_physical_devices())"

# Use CPU-only version
pip install tensorflow-cpu==2.15.0
```

---

## 📊 Kết luận

Hệ thống ML-based recommendation này cung cấp:

✅ **Multiple ML Algorithms** - Surprise, scikit-learn, TensorFlow
✅ **Comprehensive Preprocessing** - Automated data preparation
✅ **Production Ready** - Caching, monitoring, scalability
✅ **Easy Integration** - Seamless Django integration
✅ **Extensible Architecture** - Easy to add new algorithms

Hệ thống này cung cấp recommendations chính xác, scalable và maintainable cho movie recommendation platform.
