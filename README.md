# 🎬 MovieMate - Advanced Movie Recommendation System

A comprehensive, production-ready movie recommendation platform built with Django and React, featuring state-of-the-art machine learning algorithms, multi-dataset integration, and enterprise-grade architecture.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.0+-green.svg)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Overview

MovieMate is an intelligent movie recommendation system that combines multiple advanced machine learning techniques to deliver personalized movie suggestions. The platform integrates real-world datasets from IMDB and MovieLens, employs sophisticated filtering algorithms, and provides a modern, responsive user experience.

### 🎯 Key Features

- **🤖 Advanced Recommendation Algorithms**

  - Collaborative Filtering with Pearson Correlation
  - Enhanced Demographic Filtering with K-Means Clustering
  - Hybrid Recommendation Engine
  - Content-Based Filtering
  - Real-time Recommendation Updates

- **📊 Multi-Dataset Integration**

  - IMDB Dataset Integration (718K+ movies)
  - MovieLens Dataset Support (6.6K movies with ML IDs, 402K+ ratings)
  - Real-time TMDB API Synchronization (164K+ movies)
  - Automatic Data Enrichment Pipeline

- **🎨 Modern User Experience**

  - Responsive React 18+ Frontend
  - Real-time Search with Elasticsearch
  - Optimized Image Delivery
  - Multi-language Support (English/Vietnamese)
  - Admin & Moderator Dashboards
  - Content Moderation with AI

- **⚡ Performance & Scalability**
  - Redis Caching Layer
  - Celery Background Processing
  - PostgreSQL with Optimized Indexes (307K+ user similarities)
  - Elasticsearch Full-Text Search
  - Production-Ready Deployment

## 🏗️ Architecture

### System Architecture Diagram

```mermaid
graph TB
    A[Client Browser] --> B[React Frontend]
    B --> C[Django REST API]
    C --> D[PostgreSQL Database]
    C --> E[Redis Cache]
    C --> F[Elasticsearch]
    C --> G[Celery Workers]
    G --> H[IMDB API]
    G --> I[TMDB API]
    K[Admin/Moderator Dashboard] --> C
    L[ML Recommendation Engine] --> C
```

### 🧠 Machine Learning Pipeline

The recommendation system employs a sophisticated multi-stage ML pipeline:

1. **Data Preprocessing**

   - Feature engineering for demographic vectors
   - Rating matrix construction
   - Sparse matrix optimization

2. **Algorithm Ensemble**

   - **Collaborative Filtering**: User-item interactions using Pearson correlation
   - **Demographic Filtering**: K-means clustering with scikit-learn
   - **Hybrid Model**: Weighted combination of multiple algorithms
   - **Content-Based**: Genre and metadata similarity

3. **Real-time Optimization**
   - Dynamic re-ranking based on user behavior
   - A/B testing framework for algorithm tuning
   - Performance monitoring and auto-scaling

## 🔧 Tech Stack

### Backend Technologies

| Technology        | Version | Purpose                                 |
| ----------------- | ------- | --------------------------------------- |
| **Django**        | 4.0+    | Web framework and REST API              |
| **PostgreSQL**    | 13+     | Primary database with advanced indexing |
| **Redis**         | 6+      | Caching and session management          |
| **Elasticsearch** | 7.17+   | Full-text search and analytics          |
| **Celery**        | 5.2+    | Asynchronous task processing            |
| **TMDB API**      | Latest  | Movie metadata and images               |

### Machine Learning Stack

| Library                | Version | Purpose                        |
| ---------------------- | ------- | ------------------------------ |
| **NumPy**              | 2.2+    | Numerical computing            |
| **Pandas**             | 2.2+    | Data manipulation and analysis |
| **Scikit-learn**       | 1.7+    | Machine learning algorithms    |
| **SciPy**              | 1.16+   | Statistical computations       |
| **Matplotlib/Seaborn** | Latest  | Data visualization             |
| **NLTK**               | 3.9+    | Natural language processing    |

### Frontend Technologies

| Technology        | Version | Purpose                     |
| ----------------- | ------- | --------------------------- |
| **React**         | 18+     | UI framework with hooks     |
| **Redux Toolkit** | 2.8+    | State management            |
| **React Query**   | 5.76+   | Data fetching and caching   |
| **Tailwind CSS**  | Latest  | Utility-first CSS framework |
| **Framer Motion** | 12+     | Animation library           |
| **Chart.js**      | 4.5+    | Data visualization          |

## 📊 Dataset Integration

### IMDB Dataset

- **Movies**: 1M+ titles with metadata
- **Ratings**: Professional critic scores
- **Cast & Crew**: Detailed filmography data
- **Real-time Sync**: Automatic updates via IMDB API

```python
# Example: IMDB data processing
from apps.movies.services.imdb_service import IMDBService

# Sync popular movies
tconsts = IMDBService.get_popular_movies()
for imdb_id in tconsts:
    movie_data = IMDBService.get_movie_details(imdb_id)
    # Process and store in database
```

### MovieLens Dataset

- **User Demographics**: Age, gender, occupation, location
- **Ratings**: 100K to 25M user ratings
- **Temporal Data**: Rating timestamps for trend analysis
- **Research Quality**: Academic-grade dataset for ML training

```python
# Example: MovieLens integration
python manage.py import_movielens_with_demographics \
    --dataset-size=25m \
    --batch-size=1000 \
    --download
```

## 🤖 Recommendation Algorithms

### 1. Collaborative Filtering

**Algorithm**: Pearson Correlation Coefficient with user similarity

```python
class CollaborativeFilteringService:
    def calculate_user_similarity(self, user1, user2):
        # Pearson correlation for user similarity
        common_ratings = self.get_common_ratings(user1, user2)
        if len(common_ratings) < self.min_common_ratings:
            return 0.0

        # Calculate Pearson correlation
        return self.pearson_correlation(common_ratings)
```

**Features**:

- Minimum 5 common ratings for similarity calculation
- Quality gates to ensure recommendation reliability
- Cached similarity matrices for performance
- Adaptive thresholds based on user profile completeness

### 2. Enhanced Demographic Filtering

**Algorithm**: K-Means Clustering with Advanced Feature Engineering

```python
class EnhancedDemographicFilteringService:
    def create_demographic_vector(self, user):
        features = []
        # Age bins (one-hot encoded)
        features.extend(self._encode_age_bins(user.age))
        # Gender encoding
        features.extend(self._encode_gender(user.gender))
        # Occupation groups
        features.extend(self._encode_occupation_groups(user.occupation))
        # Geographic regions
        features.extend(self._encode_location(user.location))
        # Behavioral features
        features.extend(self._encode_behavioral_features(user))

        return np.array(features, dtype=np.float64)
```

**Features**:

- Multi-dimensional demographic vectors
- K-means clustering with scikit-learn
- Behavioral feature integration
- Geographic and cultural preferences

### 3. Hybrid Recommendation Engine

**Algorithm**: Weighted ensemble of multiple filtering methods

```python
class HybridRecommendationService:
    def __init__(self):
        self.weights = {
            'collaborative': 0.5,
            'demographic': 0.4,
            'trending': 0.1
        }

    def generate_hybrid_recommendations(self, user, limit=20):
        # Combine multiple recommendation sources
        collaborative_recs = self.collaborative_service.generate_recommendations(user)
        demographic_recs = self.demographic_service.generate_recommendations(user)
        trending_recs = self.get_trending_recommendations(user)

        # Weighted scoring and ranking
        return self.combine_recommendations(
            collaborative_recs, demographic_recs, trending_recs
        )
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- Elasticsearch 7+

### Quick Start

1. **Clone the repository**

```bash
git clone https://github.com/ngtrnhao/movie-mate-v2.git
cd movie-mate-v2
```

2. **Backend Setup**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements/local.txt

# Environment setup
cp backend/.env.example backend/.env
# Edit .env with your configuration

# Database setup
python backend/manage.py migrate
python backend/manage.py createsuperuser

# Start services
redis-server
elasticsearch
celery -A backend worker -l info

# Start Django development server
python backend/manage.py runserver
```

3. **Frontend Setup**

```bash
cd frontend
npm install
npm start
```

4. **Data Import (Optional)**

```bash
# Import MovieLens dataset
python backend/manage.py import_movielens_with_demographics --dataset-size=small

# Sync IMDB data
python backend/manage.py sync_popular_movies
```

### Environment Configuration

```bash
# Backend (.env)
DATABASE_URL=postgresql://username:password@localhost:5432/moviemate
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_DSL_HOST=localhost:9200
IMDB_API_KEY=your_imdb_key
TMDB_API_KEY=your_tmdb_key
```

## 🔧 Production Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale workers
docker-compose up --scale celery=3
```

### Performance Optimization

- **Database**: Optimized PostgreSQL indexes for recommendation queries
- **Caching**: Multi-layer Redis caching strategy
- **Search**: Elasticsearch with custom analyzers
- **Monitoring**: Built-in performance metrics and health checks
- **ML Optimization**: Pre-computed user similarities for fast recommendations

## 📈 Features & Services

### 🎯 Core Recommendation Services

- **PersonalizedRecommendations**: User-specific movie suggestions
- **SimilarMovieFinder**: Content-based movie similarity
- **TrendingAnalytics**: Real-time popularity tracking
- **GenreExplorer**: Genre-based discovery tools
- **DemographicClustering**: Age, gender, occupation-based recommendations

### 🔍 Advanced Search & Discovery

- **ElasticsearchService**: Full-text movie search
- **FacetedSearch**: Multi-dimensional filtering
- **AutoComplete**: Real-time search suggestions
- **SmartFiltering**: ML-powered result ranking

### 📊 Analytics & Insights

- **UserBehaviorTracking**: Interaction analytics
- **RecommendationMetrics**: Algorithm performance monitoring
- **A/BTestingFramework**: Continuous optimization
- **ProductionMetrics**: System health monitoring

### 🛡️ Content Moderation

- **SpoilerDetection**: Automatic content filtering with ML
- **ModerationDashboard**: AI-powered content review interface
- **ReportingSystem**: Community-driven moderation
- **AutomaticFlagging**: Real-time content screening
- **AdminControls**: Movie publishing and visibility management

### 🎨 User Experience

- **ResponsiveDesign**: Mobile-first approach
- **ModernUI**: React 18+ with Tailwind CSS
- **InternationalizationI18n**: Multi-language support (EN/VI)
- **UserProfiles**: Comprehensive user management system

## 📊 API Documentation

### Recommendation Endpoints

```http
GET /api/recommendations/
GET /api/recommendations/collaborative/
GET /api/recommendations/demographic/
GET /api/recommendations/hybrid/
POST /api/recommendations/feedback/
```

### Movie Management

```http
GET /api/movies/
GET /api/movies/{id}/
POST /api/movies/{id}/rate/
GET /api/movies/search/
GET /api/movies/trending/
```

### User Profile

```http
GET /api/users/profile/
PUT /api/users/profile/
GET /api/users/preferences/
POST /api/users/watchlist/
```

Full API documentation available at `/api/docs/` when running the development server.

## 🧪 Testing

### Backend Testing

```bash
# Run all tests
python backend/manage.py test

# Run specific test modules
python backend/manage.py test apps.recommendations.tests
python backend/manage.py test apps.movies.tests

# Run with coverage
coverage run --source='.' backend/manage.py test
coverage report
```

### Frontend Testing

```bash
cd frontend
npm test
npm run test:coverage
```

### ML Algorithm Evaluation

```bash
# Evaluate recommendation algorithms
python backend/manage.py evaluate_recommendations
python backend/manage.py benchmark_algorithms

# Run database analysis and visualization
python backend/scripts/check_database_status.py
python backend/scripts/comprehensive_database_analysis.py
python backend/scripts/visualize_demographic_data.py

# Generated visualizations will be saved to:
# - backend/data/demographic_visualizations/
# - backend/data/comprehensive_analysis/
```

## 📈 Performance Metrics

### System Performance

- **Database**: 718K+ movies, 402K+ ratings, 6.4K+ users
- **ML Readiness**: 5.5K users ready for CF, 6.2K for demographic filtering
- **Pre-computed**: 307K+ user similarities for fast recommendations
- **Response Time**: <200ms for cached recommendations
- **Scalability**: Production-ready with Celery background processing

### Real Dataset Statistics

- **User Coverage**: 96.1% users have demographic data
- **Rating Density**: 62.7 ratings per CF-ready user on average
- **Algorithm Mix**:
  - Collaborative Filtering: 5,529 users ready (≥5 ratings)
  - Demographic Filtering: 6,183 users ready
  - Hybrid Recommendations: Weighted combination
- **Active Clusters**: 21 demographic clusters with balanced distribution

#### 📊 Data Visualizations

<div align="center">

**User Demographics Analysis**

![User Demographics](docs/images/readme/user_demographics.png)

**Demographic Clustering Analysis**

![Cluster Analysis](docs/images/readme/cluster_analysis.png)

**Movie Database Analysis**

![Movie Analysis](docs/images/readme/movie_analysis.png)

**Collaborative Filtering Performance**

![CF Performance](docs/images/readme/cf_performance.png)

</div>

## 📈 Demographic Analysis

Detailed analysis of our user base and their movie preferences:

<div align="center">

**Gender Distribution**

![Gender Distribution](docs/images/readme/gender_distribution.png)

**Age Distribution**

![Age Distribution](docs/images/readme/age_distribution.png)

**Occupation Distribution**

![Occupation Distribution](docs/images/readme/occupation_distribution.png)

**Location Distribution**

![Location Distribution](docs/images/readme/location_distribution.png)

**User Rating Patterns**

![Rating Patterns](docs/images/readme/rating_patterns.png)

**Demographic Correlations**

![Demographic Correlations](docs/images/readme/demographic_correlations.png)

</div>

## 🔐 Security

- **Authentication**: JWT-based with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **DataProtection**: GDPR compliance
- **APISecurityRate**: limiting and request validation
- **ContentSecurity**: XSS and CSRF protection

## 🤖 Machine Learning Analysis

Comprehensive analysis of our recommendation algorithms and performance:

<div align="center">

**Collaborative Filtering Analysis**

![Collaborative Filtering](docs/images/readme/collaborative_filtering.png)

**Recommendation Results Distribution**

![Recommendation Results](docs/images/readme/recommendation_results.png)

**User Rating Patterns Analysis**

![Rating Patterns Analysis](docs/images/readme/rating_patterns.png)

</div>

## 🌍 Internationalization

- **Languages**: English, Vietnamese
- **Localization**: Date/time, currency, number formats
- **ContentTranslation**: Movie titles and descriptions
- **RTLSupport**: Right-to-left language support ready

## 🚧 Roadmap

### Q1 2026

- [ ] Deep Learning Recommendations (Neural Collaborative Filtering)
- [ ] Real-time Collaborative Filtering with Apache Kafka
- [ ] Advanced A/B Testing Framework

### Q2 2026

- [ ] Mobile Applications (React Native)
- [ ] Voice Search Integration
- [ ] Blockchain-based Review Verification

### Q3 2026

- [ ] Multi-modal Recommendations (Text + Video)
- [ ] Social Features and Friend Recommendations
- [ ] Advanced Analytics Dashboard

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- **Backend**: PEP 8, Django best practices
- **Frontend**: ESLint, Prettier, React best practices
- **Testing**: 80%+ code coverage required
- **Documentation**: Comprehensive docstrings and comments

## 📞 Support

- **Documentation**: [Wiki](https://github.com/ngtrnhao/movie-mate-v2/wiki)
- **Issues**: [GitHub Issues](https://github.com/ngtrnhao/movie-mate-v2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ngtrnhao/movie-mate-v2/discussions)
- **Email**: nguyentruongnhathao1922@gmail.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📊 Production Statistics

This MovieMate system is currently managing:

- **718,054 movies** from IMDB dataset
- **6,432 users** with comprehensive demographic data
- **402,778 user ratings** powering collaborative filtering
- **307,821 pre-computed user similarities** for fast recommendations
- **6 demographic clusters** for demographic filtering
- **49 genres** with multi-language support

## 🙏 Acknowledgments

- **MovieLens**: University of Minnesota for the MovieLens dataset
- **IMDB**: Internet Movie Database for comprehensive movie metadata
- **TMDB**: The Movie Database for additional movie information and images
- **Open Source Community**: All the amazing libraries and frameworks used

---

<div align="center">

**Built with ❤️ by the MovieMate Development Team**

[🌟 Star us on GitHub](https://github.com/ngtrnhao/movie-mate-v2/star) | [ 💡Request Feature ](https://github.com/ngtrnhao/movie-mate-v2/issues/new?template=feature_request.md) | [🐛Report Bug ](https://github.com/ngtrnhao/movie-mate-v2/issues/new?template=bug_report.md)

</div>
