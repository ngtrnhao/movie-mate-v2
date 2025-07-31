# Sơ Đồ Kiến Trúc Website Movie Recommendation System

## 1. Tổng Quan Kiến Trúc Hệ Thống

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOB[Mobile Browser]
        TAB[Tablet Browser]
    end

    subgraph "Frontend Layer (React.js)"
        REACT[React.js 18.x]
        REDUX[Redux Toolkit]
        RQ[React Query]
        ROUTER[React Router]
        UI[UI Components]
        I18N[Internationalization]
    end

    subgraph "API Gateway & Load Balancer"
        NGINX[Nginx Load Balancer]
        CDN[CDN/Static Assets]
    end

    subgraph "Backend Services (Django)"
        DJANGO[Django 4.x REST API]
        CELERY[Celery Workers]
        WSGI[Gunicorn WSGI]
        ADMIN[Django Admin]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL 15)]
        REDIS[(Redis 7.0 Cache)]
        ELASTIC[(Elasticsearch)]
    end

    subgraph "External Services"
        TMDB[TMDB API]
        IMDB[IMDB Dataset]
        PAYPAL[PayPal API]
        GOOGLE[Google OAuth]
        EMAIL[Email Service]
    end

    subgraph "Monitoring & Analytics"
        LOGS[Logging System]
        METRICS[Performance Monitoring]
        ANALYTICS[User Analytics]
    end

    %% Client to Frontend
    WEB --> REACT
    MOB --> REACT
    TAB --> REACT

    %% Frontend Internal
    REACT --> REDUX
    REACT --> RQ
    REACT --> ROUTER
    REACT --> UI
    REACT --> I18N

    %% Frontend to API Gateway
    REACT --> NGINX
    NGINX --> CDN

    %% API Gateway to Backend
    NGINX --> DJANGO
    DJANGO --> WSGI

    %% Backend to Data Layer
    DJANGO --> POSTGRES
    DJANGO --> REDIS
    DJANGO --> ELASTIC

    %% Backend to External Services
    DJANGO --> TMDB
    DJANGO --> IMDB
    DJANGO --> PAYPAL
    DJANGO --> GOOGLE
    DJANGO --> EMAIL

    %% Background Processing
    DJANGO --> CELERY
    CELERY --> POSTGRES
    CELERY --> REDIS

    %% Monitoring
    DJANGO --> LOGS
    DJANGO --> METRICS
    DJANGO --> ANALYTICS

    style REACT fill:#61dafb
    style DJANGO fill:#092e20
    style POSTGRES fill:#336791
    style REDIS fill:#dc382d
    style ELASTIC fill:#f7df1e
```

## 2. Kiến Trúc Backend (Django Apps)

```mermaid
graph TB
    subgraph "Django Applications"
        subgraph "Core Apps"
            CORE[Core App]
            API[API App]
        end

        subgraph "Business Logic Apps"
            MOVIES[Movies App]
            USERS[Users App]
            RECOMMENDATIONS[Recommendations App]
            METADATA[Metadata App]
            SUBSCRIPTIONS[Subscriptions App]
        end

        subgraph "Models & Data"
            MOVIE_MODELS[Movie Models]
            USER_MODELS[User Models]
            REC_MODELS[Recommendation Models]
            META_MODELS[Metadata Models]
        end

        subgraph "Services & Business Logic"
            MOVIE_SERVICES[Movie Services]
            USER_SERVICES[User Services]
            REC_SERVICES[Recommendation Services]
            ML_SERVICES[ML Algorithms]
        end

        subgraph "API Endpoints"
            MOVIE_API[Movie API]
            USER_API[User API]
            REC_API[Recommendation API]
            AUTH_API[Authentication API]
        end
    end

    %% Core connections
    CORE --> API
    API --> MOVIES
    API --> USERS
    API --> RECOMMENDATIONS
    API --> METADATA
    API --> SUBSCRIPTIONS

    %% Models
    MOVIES --> MOVIE_MODELS
    USERS --> USER_MODELS
    RECOMMENDATIONS --> REC_MODELS
    METADATA --> META_MODELS

    %% Services
    MOVIES --> MOVIE_SERVICES
    USERS --> USER_SERVICES
    RECOMMENDATIONS --> REC_SERVICES
    RECOMMENDATIONS --> ML_SERVICES

    %% API Endpoints
    MOVIES --> MOVIE_API
    USERS --> USER_API
    RECOMMENDATIONS --> REC_API
    USERS --> AUTH_API

    style MOVIES fill:#ff6b35
    style USERS fill:#4ecdc4
    style RECOMMENDATIONS fill:#45b7d1
    style API fill:#96ceb4
```

## 3. Kiến Trúc Database (PostgreSQL)

```mermaid
graph TB
    subgraph "PostgreSQL Database Schema"
        subgraph "Movie Management"
            MOVIES_TABLE[Movies Table]
            MOVIE_METADATA[Movie Metadata]
            MOVIE_GENRES[Movie Genres]
            MOVIE_CAST[Movie Cast]
            MOVIE_TRAILERS[Movie Trailers]
            MOVIE_IMAGES[Movie Images]
            MOVIE_RATINGS[Movie Ratings]
            MOVIE_REVIEWS[Movie Reviews]
        end

        subgraph "User Management"
            USERS_TABLE[Users Table]
            USER_PREFERENCES[User Preferences]
            USER_FAVORITES[User Favorites]
            WATCHLISTS[Watchlists]
            SEARCH_HISTORY[Search History]
        end

        subgraph "Recommendation System"
            USER_PREFERENCES_REC[User Preferences]
            USER_SIMILARITY[User Similarity]
            MOVIE_SIMILARITY[Movie Similarity]
            RECOMMENDATION_RESULTS[Recommendation Results]
            DEMOGRAPHIC_CLUSTERS[Demographic Clusters]
        end

        subgraph "Content Management"
            GENRES_TABLE[Genres Table]
            PERSONS_TABLE[Persons Table]
            PRODUCTION_COMPANIES[Production Companies]
        end

        subgraph "Admin & Moderation"
            MOVIE_ADMIN_CONTROL[Movie Admin Control]
            MOVIE_QUALITY_METRICS[Movie Quality Metrics]
            MOVIE_SCHEDULING[Movie Scheduling]
            MODERATION_CONFIG[Moderation Config]
            REVIEW_REPORTS[Review Reports]
        end

        subgraph "Analytics & Metrics"
            USER_INTERACTIONS[User Interactions]
            PRODUCTION_METRICS[Production Metrics]
            RECOMMENDATION_METRICS[Recommendation Metrics]
        end
    end

    %% Movie relationships
    MOVIES_TABLE --> MOVIE_METADATA
    MOVIES_TABLE --> MOVIE_GENRES
    MOVIES_TABLE --> MOVIE_CAST
    MOVIES_TABLE --> MOVIE_TRAILERS
    MOVIES_TABLE --> MOVIE_IMAGES
    MOVIES_TABLE --> MOVIE_RATINGS
    MOVIES_TABLE --> MOVIE_REVIEWS

    %% User relationships
    USERS_TABLE --> USER_PREFERENCES
    USERS_TABLE --> USER_FAVORITES
    USERS_TABLE --> WATCHLISTS
    USERS_TABLE --> SEARCH_HISTORY

    %% Recommendation relationships
    USERS_TABLE --> USER_PREFERENCES_REC
    USERS_TABLE --> USER_SIMILARITY
    MOVIES_TABLE --> MOVIE_SIMILARITY
    USERS_TABLE --> RECOMMENDATION_RESULTS
    USERS_TABLE --> DEMOGRAPHIC_CLUSTERS

    %% Admin relationships
    MOVIES_TABLE --> MOVIE_ADMIN_CONTROL
    MOVIES_TABLE --> MOVIE_QUALITY_METRICS
    MOVIES_TABLE --> MOVIE_SCHEDULING
    MOVIE_REVIEWS --> MODERATION_CONFIG
    MOVIE_REVIEWS --> REVIEW_REPORTS

    %% Analytics relationships
    MOVIES_TABLE --> USER_INTERACTIONS
    MOVIES_TABLE --> PRODUCTION_METRICS
    RECOMMENDATION_RESULTS --> RECOMMENDATION_METRICS

    style MOVIES_TABLE fill:#ff6b35
    style USERS_TABLE fill:#4ecdc4
    style RECOMMENDATION_RESULTS fill:#45b7d1
```

## 4. Kiến Trúc Frontend (React.js)

```mermaid
graph TB
    subgraph "React Frontend Architecture"
        subgraph "Core Application"
            APP[App.jsx]
            INDEX[index.js]
            ROUTES[React Router]
        end

        subgraph "State Management"
            REDUX_STORE[Redux Store]
            AUTH_SLICE[Auth Slice]
            MOVIE_SLICE[Movie Slice]
            FAVORITES_SLICE[Favorites Slice]
            DASHBOARD_SLICE[Dashboard Slice]
        end

        subgraph "Data Fetching"
            REACT_QUERY[React Query]
            API_CLIENT[API Client]
            AXIOS[Axios]
        end

        subgraph "UI Components"
            PAGES[Pages]
            COMPONENTS[Components]
            LAYOUTS[Layouts]
            MODALS[Modals]
        end

        subgraph "Features"
            AUTH[Authentication]
            MOVIES[Movie Management]
            RECOMMENDATIONS[Recommendations]
            PROFILE[User Profile]
            ADMIN[Admin Dashboard]
            MODERATOR[Moderator Dashboard]
        end

        subgraph "Utilities"
            HOOKS[Custom Hooks]
            UTILS[Utility Functions]
            I18N[Internationalization]
            STYLES[Styling]
        end
    end

    %% Core connections
    INDEX --> APP
    APP --> ROUTES
    ROUTES --> PAGES

    %% State management
    APP --> REDUX_STORE
    REDUX_STORE --> AUTH_SLICE
    REDUX_STORE --> MOVIE_SLICE
    REDUX_STORE --> FAVORITES_SLICE
    REDUX_STORE --> DASHBOARD_SLICE

    %% Data fetching
    PAGES --> REACT_QUERY
    REACT_QUERY --> API_CLIENT
    API_CLIENT --> AXIOS

    %% UI components
    PAGES --> COMPONENTS
    PAGES --> LAYOUTS
    PAGES --> MODALS

    %% Features
    PAGES --> AUTH
    PAGES --> MOVIES
    PAGES --> RECOMMENDATIONS
    PAGES --> PROFILE
    PAGES --> ADMIN
    PAGES --> MODERATOR

    %% Utilities
    COMPONENTS --> HOOKS
    COMPONENTS --> UTILS
    COMPONENTS --> I18N
    COMPONENTS --> STYLES

    style APP fill:#61dafb
    style REDUX_STORE fill:#764abc
    style REACT_QUERY fill:#ff4154
```

## 5. Kiến Trúc Recommendation System

```mermaid
graph TB
    subgraph "Recommendation Engine"
        subgraph "Data Sources"
            USER_RATINGS[User Ratings]
            MOVIE_METADATA[Movie Metadata]
            USER_PROFILES[User Profiles]
            INTERACTION_DATA[Interaction Data]
        end

        subgraph "Algorithms"
            COLLABORATIVE[Collaborative Filtering]
            CONTENT_BASED[Content-Based Filtering]
            DEMOGRAPHIC[Demographic Filtering]
            HYBRID[Hybrid Algorithm]
        end

        subgraph "ML Services"
            SIMILARITY_CALC[Similarity Calculation]
            CLUSTERING[User Clustering]
            RATING_PREDICTION[Rating Prediction]
            FEATURE_EXTRACTION[Feature Extraction]
        end

        subgraph "Recommendation Types"
            PERSONALIZED[Personalized Recommendations]
            TRENDING[Trending Movies]
            POPULAR[Popular Movies]
            SIMILAR_MOVIES[Similar Movies]
            GENRE_BASED[Genre-Based]
        end

        subgraph "Storage & Caching"
            REC_RESULTS[Recommendation Results]
            SIMILARITY_MATRIX[Similarity Matrix]
            USER_PREFERENCES[User Preferences]
            CACHE[Redis Cache]
        end
    end

    %% Data flow
    USER_RATINGS --> COLLABORATIVE
    MOVIE_METADATA --> CONTENT_BASED
    USER_PROFILES --> DEMOGRAPHIC
    INTERACTION_DATA --> HYBRID

    %% Algorithm processing
    COLLABORATIVE --> SIMILARITY_CALC
    CONTENT_BASED --> FEATURE_EXTRACTION
    DEMOGRAPHIC --> CLUSTERING
    HYBRID --> RATING_PREDICTION

    %% Recommendation generation
    SIMILARITY_CALC --> PERSONALIZED
    FEATURE_EXTRACTION --> SIMILAR_MOVIES
    CLUSTERING --> GENRE_BASED
    RATING_PREDICTION --> TRENDING

    %% Storage
    PERSONALIZED --> REC_RESULTS
    SIMILAR_MOVIES --> SIMILARITY_MATRIX
    GENRE_BASED --> USER_PREFERENCES
    TRENDING --> CACHE

    style COLLABORATIVE fill:#ff6b35
    style CONTENT_BASED fill:#4ecdc4
    style HYBRID fill:#45b7d1
    style PERSONALIZED fill:#96ceb4
```

## 6. Kiến Trúc Deployment & Infrastructure

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Load Balancer & CDN"
            LB[Load Balancer]
            CDN[CDN]
            SSL[SSL Termination]
        end

        subgraph "Application Servers"
            WEB1[Web Server 1]
            WEB2[Web Server 2]
            WEB3[Web Server 3]
        end

        subgraph "Background Workers"
            CELERY1[Celery Worker 1]
            CELERY2[Celery Worker 2]
            CELERY3[Celery Worker 3]
            BEAT[Celery Beat]
            FLOWER[Flower Monitor]
        end

        subgraph "Database Cluster"
            DB_MASTER[(Master DB)]
            DB_SLAVE1[(Slave DB 1)]
            DB_SLAVE2[(Slave DB 2)]
        end

        subgraph "Cache & Search"
            REDIS_MASTER[(Redis Master)]
            REDIS_SLAVE1[(Redis Slave 1)]
            REDIS_SLAVE2[(Redis Slave 2)]
            ELASTIC_CLUSTER[(Elasticsearch Cluster)]
        end

        subgraph "Monitoring & Logging"
            MONITOR[Monitoring]
            LOGS[Log Aggregation]
            ALERTS[Alerting]
            ANALYTICS[Analytics]
        end
    end

    %% Load balancer connections
    LB --> SSL
    SSL --> WEB1
    SSL --> WEB2
    SSL --> WEB3

    %% Application server connections
    WEB1 --> CELERY1
    WEB2 --> CELERY2
    WEB3 --> CELERY3
    WEB1 --> BEAT
    WEB1 --> FLOWER

    %% Database connections
    WEB1 --> DB_MASTER
    WEB2 --> DB_MASTER
    WEB3 --> DB_MASTER
    DB_MASTER --> DB_SLAVE1
    DB_MASTER --> DB_SLAVE2

    %% Cache connections
    WEB1 --> REDIS_MASTER
    WEB2 --> REDIS_MASTER
    WEB3 --> REDIS_MASTER
    REDIS_MASTER --> REDIS_SLAVE1
    REDIS_MASTER --> REDIS_SLAVE2

    %% Search connections
    WEB1 --> ELASTIC_CLUSTER
    WEB2 --> ELASTIC_CLUSTER
    WEB3 --> ELASTIC_CLUSTER

    %% Monitoring connections
    WEB1 --> MONITOR
    WEB2 --> MONITOR
    WEB3 --> MONITOR
    MONITOR --> LOGS
    MONITOR --> ALERTS
    MONITOR --> ANALYTICS

    style LB fill:#ff6b35
    style DB_MASTER fill:#336791
    style REDIS_MASTER fill:#dc382d
    style ELASTIC_CLUSTER fill:#f7df1e
```

## 7. Technology Stack Summary

### 7.1. Frontend Stack

- **React.js 18.x** - Main frontend framework
- **Redux Toolkit** - State management
- **React Query** - Data fetching and caching
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **React Hook Form** - Form management
- **Framer Motion** - Animation library
- **i18next** - Internationalization
- **Chart.js** - Data visualization

### 7.2. Backend Stack

- **Django 4.x** - Web framework
- **Django REST Framework** - API framework
- **PostgreSQL 15** - Primary database
- **Redis 7.0** - Caching and message broker
- **Elasticsearch** - Search engine
- **Celery** - Background task processing
- **JWT** - Authentication
- **Django CORS Headers** - Cross-origin resource sharing

### 7.3. DevOps & Infrastructure

- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy and load balancer
- **Gunicorn** - WSGI server
- **PostgreSQL** - Database
- **Redis** - Cache and message broker
- **Elasticsearch** - Search engine
- **Celery Workers** - Background tasks

### 7.4. External Services

- **TMDB API** - Movie data source
- **IMDB Dataset** - Movie ratings and metadata
- **PayPal API** - Payment processing
- **Google OAuth** - Authentication
- **Email Service** - SMTP/SendGrid

## 8. Key Features & Capabilities

### 8.1. Movie Management

- Comprehensive movie database with metadata
- Multi-language support (English/Vietnamese)
- Movie ratings and reviews system
- Cast and crew information
- Trailer and image management
- Quality metrics and content moderation

### 8.2. User Management

- User authentication and authorization
- Profile management with demographics
- Watchlist and favorites
- Search history tracking
- Email verification system
- Subscription management

### 8.3. Recommendation System

- Collaborative filtering
- Content-based filtering
- Demographic filtering
- Hybrid recommendation algorithms
- Real-time recommendation generation
- User similarity calculations

### 8.4. Admin & Moderation

- Admin dashboard for content management
- Moderator dashboard for review moderation
- Content quality assessment
- Automated spoiler detection
- User interaction analytics
- Performance metrics tracking

### 8.5. Performance & Scalability

- Redis caching for improved performance
- Elasticsearch for fast search
- Database optimization with indexing
- Background task processing with Celery
- CDN for static assets
- Load balancing for horizontal scaling

## 9. Security & Compliance

### 9.1. Authentication & Authorization

- JWT-based authentication
- Role-based access control
- Secure password hashing
- Session management
- CSRF protection

### 9.2. Data Protection

- Encrypted data transmission (HTTPS)
- Secure database connections
- Input validation and sanitization
- SQL injection prevention
- XSS protection

### 9.3. API Security

- Rate limiting
- API key management
- Request validation
- Error handling
- Audit logging

## 10. Monitoring & Analytics

### 10.1. Application Monitoring

- Performance metrics tracking
- Error monitoring and alerting
- User behavior analytics
- Recommendation system metrics
- Database performance monitoring

### 10.2. Infrastructure Monitoring

- Server resource monitoring
- Database performance tracking
- Cache hit/miss ratios
- Network latency monitoring
- Automated alerting

### 10.3. Business Analytics

- User engagement metrics
- Content popularity tracking
- Recommendation effectiveness
- Revenue analytics
- User retention analysis

---

_Sơ đồ kiến trúc này thể hiện cấu trúc toàn diện của hệ thống Movie Recommendation System với các thành phần chính, luồng dữ liệu và mối quan hệ giữa các module._
