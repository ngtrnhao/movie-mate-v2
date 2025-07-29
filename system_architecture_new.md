# Kiến Trúc Chi Tiết Dự Án Movie Recommendation System

## 1. Tổng Quan Kiến Trúc Hệ Thống

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOB[Mobile Browser]
        TAB[Tablet Browser]
    end

    subgraph "Frontend Layer (React.js)"
        REACT[React.js 18.2.0]
        REDUX[Redux Toolkit]
        RQ[React Query v5]
        ROUTER[React Router v6]
        TAILWIND[Tailwind CSS]
        MUI[Material-UI v7]
        FRAMER[Framer Motion]
    end

    subgraph "API Gateway & Load Balancer"
        NGINX[Nginx]
        CDN[CDN/Static Assets]
        CORS[CORS Headers]
    end

    subgraph "Backend Services (Django)"
        DJANGO[Django 4.x + DRF]
        CELERY[Celery Workers]
        WSGI[Gunicorn WSGI]
        WHITENOISE[WhiteNoise Static]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis Cloud)]
        ELASTIC[(Elasticsearch Cloud)]
    end

    subgraph "External Services"
        TMDB[TMDB API]
        IMDB[IMDB RapidAPI]
        PAYPAL[PayPal API]
        GOOGLE[Google OAuth]
        EMAIL[SMTP Email]
    end

    subgraph "Monitoring & Analytics"
        LOGS[Structured Logging]
        METRICS[Performance Metrics]
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
    REACT --> TAILWIND
    REACT --> MUI
    REACT --> FRAMER

    %% Frontend to API Gateway
    REACT --> NGINX
    NGINX --> CDN
    NGINX --> CORS

    %% API Gateway to Backend
    NGINX --> DJANGO
    DJANGO --> WSGI
    DJANGO --> WHITENOISE

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

## 2. Kiến Trúc Backend Chi Tiết

### 2.1. Django Application Structure

```mermaid
graph TB
    subgraph "Django Project Structure"
        subgraph "Core Apps"
            CORE[apps.core]
            API[apps.api]
            USERS[apps.users]
            MOVIES[apps.movies]
            METADATA[apps.metadata]
            RECS[apps.recommendations]
            SUBS[apps.subscriptions]
        end

        subgraph "Configuration"
            CONFIG[config/]
            SETTINGS[settings/]
            URLS[urls.py]
            CELERY[celery.py]
        end

        subgraph "Third Party Apps"
            DRF[djangorestframework]
            JWT[rest_framework_simplejwt]
            CORS[django-cors-headers]
            FILTER[django-filter]
            REDIS[django-redis]
            ELASTIC[django-elasticsearch-dsl]
            CELERY_DJANGO[django-celery-beat]
            WHITENOISE[whitenoise]
        end
    end

    CONFIG --> CORE
    CONFIG --> API
    CONFIG --> USERS
    CONFIG --> MOVIES
    CONFIG --> METADATA
    CONFIG --> RECS
    CONFIG --> SUBS

    SETTINGS --> DRF
    SETTINGS --> JWT
    SETTINGS --> CORS
    SETTINGS --> FILTER
    SETTINGS --> REDIS
    SETTINGS --> ELASTIC
    SETTINGS --> CELERY_DJANGO
    SETTINGS --> WHITENOISE

    style CORE fill:#ff6b35
    style API fill:#61dafb
    style USERS fill:#4ecdc4
    style MOVIES fill:#45b7d1
    style RECS fill:#96ceb4
```

### 2.2. Database Schema Architecture

```mermaid
graph TB
    subgraph "PostgreSQL Database Schema"
        subgraph "User Management"
            USER[User Model]
            USER_PREF[UserPreference]
            USER_FAV[UserFavoriteMovie]
            USER_GENRE[UserFavoriteGenre]
            COMMENT[Comment]
            COMMENT_LIKE[CommentLike]
        end

        subgraph "Movie Management"
            MOVIE[Movie Model]
            MOVIE_META[MovieMetadata]
            MOVIE_GENRE[MovieGenre]
            MOVIE_CAST[MovieCast]
            MOVIE_TRAILER[MovieTrailer]
            MOVIE_IMAGE[MovieImage]
            MOVIE_RATING[MovieRating]
        end

        subgraph "Review System"
            REVIEW[MovieReview]
            REVIEW_VOTE[ReviewVote]
            REVIEW_REPORT[ReviewReport]
            MODERATION[ModerationConfig]
            MOD_FEEDBACK[ModerationFeedback]
        end

        subgraph "Recommendation System"
            USER_PREF_REC[UserPreference]
            USER_SIM[UserSimilarity]
            MOVIE_SIM[MovieSimilarity]
            REC_RESULT[RecommendationResult]
            DEMO_CLUSTER[DemographicCluster]
            REC_METRICS[RecommendationMetrics]
        end

        subgraph "Subscription & Payment"
            PAYMENT[PaymentTransaction]
            SUBSCRIPTION[Subscription]
        end

        subgraph "Analytics & Monitoring"
            USER_INTERACTION[UserInteraction]
            PROD_METRICS[ProductionMetrics]
            QUALITY_METRICS[MovieQualityMetrics]
            SCHEDULING[MovieScheduling]
        end
    end

    USER --> USER_PREF
    USER --> USER_FAV
    USER --> USER_GENRE
    USER --> COMMENT
    COMMENT --> COMMENT_LIKE

    MOVIE --> MOVIE_META
    MOVIE --> MOVIE_GENRE
    MOVIE --> MOVIE_CAST
    MOVIE --> MOVIE_TRAILER
    MOVIE --> MOVIE_IMAGE
    MOVIE --> MOVIE_RATING

    MOVIE --> REVIEW
    REVIEW --> REVIEW_VOTE
    REVIEW --> REVIEW_REPORT
    REVIEW --> MODERATION
    MODERATION --> MOD_FEEDBACK

    USER --> USER_PREF_REC
    USER --> USER_SIM
    MOVIE --> MOVIE_SIM
    USER --> REC_RESULT
    USER --> DEMO_CLUSTER
    REC_RESULT --> REC_METRICS

    USER --> PAYMENT
    USER --> SUBSCRIPTION

    USER --> USER_INTERACTION
    MOVIE --> PROD_METRICS
    MOVIE --> QUALITY_METRICS
    MOVIE --> SCHEDULING

    style USER fill:#4ecdc4
    style MOVIE fill:#45b7d1
    style REVIEW fill:#96ceb4
    style REC_RESULT fill:#ff6b35
```

### 2.3. API Architecture

```mermaid
graph TB
    subgraph "REST API Structure"
        subgraph "Authentication Endpoints"
            AUTH_REGISTER[POST /api/auth/register/]
            AUTH_LOGIN[POST /api/auth/login/]
            AUTH_REFRESH[POST /api/auth/refresh/]
            AUTH_LOGOUT[POST /api/auth/logout/]
            AUTH_GOOGLE[POST /api/auth/google/]
        end

        subgraph "User Management"
            USER_PROFILE[GET/PATCH /api/auth/profile/]
            USER_AVATAR[POST /api/auth/avatar/]
            USER_STATS[GET /api/auth/usage-stats/]
            USER_WATCHLIST[GET /api/auth/watchlist/]
            USER_FAVORITES[GET /api/auth/favorites/]
        end

        subgraph "Movie Discovery"
            MOVIE_FEATURED[GET /api/movies/featured/]
            MOVIE_TRENDING[GET /api/movies/trending/]
            MOVIE_TOP_RATED[GET /api/movies/top-rated/]
            MOVIE_UPCOMING[GET /api/movies/upcoming/]
            MOVIE_SEARCH[GET /api/movies/search/]
            MOVIE_DETAIL[GET /api/movies/{slug}/]
        end

        subgraph "Review System"
            REVIEW_CREATE[POST /api/movies/{id}/reviews/]
            REVIEW_LIST[GET /api/movies/{id}/reviews/]
            REVIEW_DETAIL[GET /api/movies/{id}/reviews/{id}/]
            SPOILER_DETECT[POST /api/movies/spoiler-detect/]
        end

        subgraph "Recommendation System"
            REC_PERSONALIZED[GET /api/recommendations/personalized/]
            REC_COLLABORATIVE[GET /api/recommendations/collaborative/]
            REC_DEMOGRAPHIC[GET /api/recommendations/demographic/]
            REC_HYBRID[GET /api/recommendations/hybrid/]
            REC_FEEDBACK[POST /api/recommendations/feedback/]
        end

        subgraph "Admin & Moderation"
            ADMIN_DASHBOARD[GET /api/admin/dashboard/]
            MODERATION_QUEUE[GET /api/moderator/queue/]
            MODERATION_STATS[GET /api/moderator/stats/]
            MODERATION_ACTION[POST /api/moderator/moderate/]
        end
    end

    AUTH_REGISTER --> USER_PROFILE
    AUTH_LOGIN --> USER_PROFILE
    USER_PROFILE --> MOVIE_DETAIL
    MOVIE_DETAIL --> REVIEW_CREATE
    MOVIE_DETAIL --> REC_PERSONALIZED

    style AUTH_REGISTER fill:#4ecdc4
    style MOVIE_DETAIL fill:#45b7d1
    style REC_PERSONALIZED fill:#ff6b35
```

## 3. Frontend Architecture Chi Tiết

### 3.1. React Application Structure

```mermaid
graph TB
    subgraph "Frontend Architecture"
        subgraph "Core Components"
            APP[App.jsx]
            ROUTER[Router]
            LAYOUT[Layout]
            NAVBAR[Navbar]
            FOOTER[Footer]
        end

        subgraph "Pages"
            HOME[Home Page]
            MOVIE_DETAIL[Movie Detail]
            SEARCH[Search Page]
            PROFILE[User Profile]
            ADMIN[Admin Dashboard]
            MODERATOR[Moderator Dashboard]
            AUTH[Authentication]
        end

        subgraph "State Management"
            REDUX_STORE[Redux Store]
            USER_SLICE[User Slice]
            MOVIE_SLICE[Movie Slice]
            AUTH_SLICE[Auth Slice]
            UI_SLICE[UI Slice]
        end

        subgraph "Data Fetching"
            RQ_CLIENT[React Query]
            API_SERVICES[API Services]
            CACHE[Query Cache]
            MUTATIONS[Mutations]
        end

        subgraph "UI Components"
            BUTTONS[Buttons]
            FORMS[Forms]
            CARDS[Movie Cards]
            MODALS[Modals]
            CHARTS[Charts]
            FILTERS[Filters]
        end

        subgraph "Utilities"
            HOOKS[Custom Hooks]
            UTILS[Utilities]
            VALIDATION[Validation]
            I18N[Internationalization]
        end
    end

    APP --> ROUTER
    ROUTER --> LAYOUT
    LAYOUT --> NAVBAR
    LAYOUT --> FOOTER

    ROUTER --> HOME
    ROUTER --> MOVIE_DETAIL
    ROUTER --> SEARCH
    ROUTER --> PROFILE
    ROUTER --> ADMIN
    ROUTER --> MODERATOR
    ROUTER --> AUTH

    APP --> REDUX_STORE
    REDUX_STORE --> USER_SLICE
    REDUX_STORE --> MOVIE_SLICE
    REDUX_STORE --> AUTH_SLICE
    REDUX_STORE --> UI_SLICE

    APP --> RQ_CLIENT
    RQ_CLIENT --> API_SERVICES
    RQ_CLIENT --> CACHE
    RQ_CLIENT --> MUTATIONS

    HOME --> BUTTONS
    MOVIE_DETAIL --> CARDS
    SEARCH --> FILTERS
    ADMIN --> CHARTS
    AUTH --> FORMS

    APP --> HOOKS
    APP --> UTILS
    APP --> VALIDATION
    APP --> I18N

    style APP fill:#61dafb
    style REDUX_STORE fill:#764abc
    style RQ_CLIENT fill:#ff4154
```

### 3.2. Frontend Technology Stack

```mermaid
graph TB
    subgraph "Frontend Dependencies"
        subgraph "Core Framework"
            REACT_CORE[React 18.2.0]
            REACT_DOM[React DOM]
            REACT_SCRIPTS[React Scripts]
        end

        subgraph "State Management"
            REDUX_TOOLKIT[Redux Toolkit 2.8.1]
            REACT_REDUX[React Redux 9.2.0]
            IMMER[Immer 10.1.1]
        end

        subgraph "Data Fetching"
            REACT_QUERY[React Query 5.76.0]
            AXIOS[Axios 1.9.0]
            REACT_QUERY_DEV[React Query DevTools]
        end

        subgraph "Routing & Navigation"
            REACT_ROUTER[React Router DOM 6.30.0]
            REACT_SCROLL[React Scroll]
        end

        subgraph "UI & Styling"
            TAILWIND_CSS[Tailwind CSS]
            MATERIAL_UI[Material-UI 7.1.1]
            HEADLESS_UI[Headless UI 2.2.4]
            HEROICONS[Heroicons 2.2.0]
            LUCIDE[Lucide React]
            FRAMER_MOTION[Framer Motion 12.9.4]
        end

        subgraph "Charts & Visualization"
            CHART_JS[Chart.js 4.5.0]
            REACT_CHARTJS[React ChartJS 2 5.3.0]
        end

        subgraph "External Integrations"
            PAYPAL_JS[PayPal React 8.8.3]
            GOOGLE_OAUTH[Google OAuth 0.12.2]
        end

        subgraph "Performance & Optimization"
            REACT_WINDOW[React Window 1.8.11]
            INTERSECTION_OBSERVER[React Intersection Observer]
            SWIPER[Swiper 11.2.6]
        end

        subgraph "Development Tools"
            ESLINT[ESLint]
            PRETTIER[Prettier]
            TESTING_LIB[Testing Library]
            WEBPACK_ANALYZER[Webpack Bundle Analyzer]
        end
    end

    REACT_CORE --> REACT_DOM
    REACT_CORE --> REACT_SCRIPTS

    REACT_CORE --> REDUX_TOOLKIT
    REDUX_TOOLKIT --> REACT_REDUX
    REDUX_TOOLKIT --> IMMER

    REACT_CORE --> REACT_QUERY
    REACT_QUERY --> AXIOS
    REACT_QUERY --> REACT_QUERY_DEV

    REACT_CORE --> REACT_ROUTER
    REACT_ROUTER --> REACT_SCROLL

    REACT_CORE --> TAILWIND_CSS
    REACT_CORE --> MATERIAL_UI
    MATERIAL_UI --> HEADLESS_UI
    MATERIAL_UI --> HEROICONS
    REACT_CORE --> LUCIDE
    REACT_CORE --> FRAMER_MOTION

    REACT_CORE --> CHART_JS
    CHART_JS --> REACT_CHARTJS

    REACT_CORE --> PAYPAL_JS
    REACT_CORE --> GOOGLE_OAUTH

    REACT_CORE --> REACT_WINDOW
    REACT_CORE --> INTERSECTION_OBSERVER
    REACT_CORE --> SWIPER

    style REACT_CORE fill:#61dafb
    style REDUX_TOOLKIT fill:#764abc
    style REACT_QUERY fill:#ff4154
```

## 4. Data Flow Architecture

### 4.1. User Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Gateway
    participant B as Backend
    participant D as Database
    participant R as Redis

    U->>F: Access Protected Route
    F->>F: Check JWT Token
    alt Token Valid
        F->>F: Allow Access
    else Token Invalid/Expired
        F->>A: POST /api/auth/refresh/
        A->>B: Refresh Token
        B->>R: Validate Refresh Token
        R-->>B: Token Valid
        B-->>A: New Access Token
        A-->>F: New Token
        F->>F: Update Token & Allow Access
    else No Token
        F->>A: POST /api/auth/login/
        A->>B: Authenticate User
        B->>D: Verify Credentials
        D-->>B: User Data
        B->>R: Store Session
        B-->>A: JWT Tokens
        A-->>F: Tokens
        F->>F: Store Tokens & Redirect
    end
```

### 4.2. Movie Recommendation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Gateway
    participant B as Backend
    participant R as Redis Cache
    participant D as Database
    participant C as Celery
    participant E as Elasticsearch

    U->>F: Request Recommendations
    F->>A: GET /api/recommendations/personalized/
    A->>B: Process Request
    B->>R: Check Cache

    alt Cache Hit
        R-->>B: Cached Recommendations
        B-->>A: Return Cached Data
        A-->>F: Recommendations
        F-->>U: Display Movies
    else Cache Miss
        B->>D: Check User Profile
        D-->>B: User Data

        alt Profile Complete
            B->>C: Trigger Background Task
            C->>E: Search Similar Users
            C->>D: Get User Ratings
            C->>D: Calculate Recommendations
            C->>R: Cache Results
            B-->>A: Popular Movies (Immediate)
            A-->>F: Popular Movies
            F-->>U: Display Popular Movies

            C-->>B: Task Complete
            B->>R: Store Recommendations
        else Profile Incomplete
            B->>D: Get Popular Movies
            D-->>B: Popular Movies
            B-->>A: Popular Movies
            A-->>F: Popular Movies
            F-->>U: Display Popular Movies
        end
    end
```

### 4.3. Movie Search Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Gateway
    participant B as Backend
    participant E as Elasticsearch
    participant D as Database
    participant R as Redis

    U->>F: Search Movies
    F->>A: GET /api/movies/search/?q=query
    A->>B: Process Search

    B->>E: Search Index
    E-->>B: Search Results

    B->>R: Check Cache
    alt Cache Hit
        R-->>B: Cached Results
    else Cache Miss
        B->>D: Get Movie Details
        D-->>B: Movie Data
        B->>R: Cache Results
    end

    B-->>A: Search Results
    A-->>F: Results
    F-->>U: Display Results
```

## 5. Deployment Architecture

### 5.1. Production Environment (Render.com)

```mermaid
graph TB
    subgraph "Production Deployment (Render.com)"
        subgraph "Load Balancer"
            RENDER_LB[Render Load Balancer]
            SSL[SSL Termination]
        end

        subgraph "Web Service"
            DJANGO_APP[Django Web Service]
            GUNICORN[Gunicorn WSGI]
            WHITENOISE[WhiteNoise Static]
        end

        subgraph "Background Workers"
            CELERY_WORKER[Celery Worker]
            CELERY_BEAT[Celery Beat Scheduler]
        end

        subgraph "Database Services"
            POSTGRES_DB[(PostgreSQL Database)]
            REDIS_CACHE[(Redis Cloud)]
            ELASTIC_SEARCH[(Elasticsearch Cloud)]
        end

        subgraph "External Services"
            FRONTEND[Vercel Frontend]
            CDN[CDN Assets]
        end
    end

    RENDER_LB --> SSL
    SSL --> DJANGO_APP
    DJANGO_APP --> GUNICORN
    DJANGO_APP --> WHITENOISE

    DJANGO_APP --> CELERY_WORKER
    DJANGO_APP --> CELERY_BEAT

    DJANGO_APP --> POSTGRES_DB
    DJANGO_APP --> REDIS_CACHE
    DJANGO_APP --> ELASTIC_SEARCH

    FRONTEND --> RENDER_LB
    DJANGO_APP --> CDN

    style DJANGO_APP fill:#092e20
    style POSTGRES_DB fill:#336791
    style REDIS_CACHE fill:#dc382d
    style ELASTIC_SEARCH fill:#f7df1e
```

### 5.2. Development Environment

```mermaid
graph TB
    subgraph "Development Environment"
        subgraph "Local Development"
            DJANGO_DEV[Django Dev Server]
            REACT_DEV[React Dev Server]
            POSTGRES_LOCAL[(Local PostgreSQL)]
            REDIS_LOCAL[(Local Redis)]
            ELASTIC_LOCAL[(Local Elasticsearch)]
        end

        subgraph "Development Tools"
            CELERY_DEV[Celery Worker Dev]
            CELERY_BEAT_DEV[Celery Beat Dev]
            FLOWER[Flower Monitoring]
        end

        subgraph "External APIs"
            TMDB_API[TMDB API]
            IMDB_API[IMDB RapidAPI]
            PAYPAL_SANDBOX[PayPal Sandbox]
            GOOGLE_DEV[Google OAuth Dev]
        end
    end

    DJANGO_DEV --> POSTGRES_LOCAL
    DJANGO_DEV --> REDIS_LOCAL
    DJANGO_DEV --> ELASTIC_LOCAL

    DJANGO_DEV --> CELERY_DEV
    DJANGO_DEV --> CELERY_BEAT_DEV
    CELERY_DEV --> FLOWER

    DJANGO_DEV --> TMDB_API
    DJANGO_DEV --> IMDB_API
    DJANGO_DEV --> PAYPAL_SANDBOX
    DJANGO_DEV --> GOOGLE_DEV

    REACT_DEV --> DJANGO_DEV

    style DJANGO_DEV fill:#092e20
    style REACT_DEV fill:#61dafb
```

## 6. Security Architecture

### 6.1. Authentication & Authorization

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Frontend Security"
            JWT_STORAGE[JWT Storage]
            TOKEN_REFRESH[Token Refresh]
            ROUTE_GUARDS[Route Guards]
        end

        subgraph "API Security"
            CORS_POLICY[CORS Policy]
            RATE_LIMITING[Rate Limiting]
            JWT_AUTH[JWT Authentication]
            PERMISSION_CLASSES[Permission Classes]
        end

        subgraph "Data Security"
            PASSWORD_HASHING[Password Hashing]
            DATA_ENCRYPTION[Data Encryption]
            SQL_INJECTION[SQL Injection Prevention]
            XSS_PROTECTION[XSS Protection]
        end

        subgraph "Infrastructure Security"
            HTTPS[HTTPS/SSL]
            FIREWALL[Firewall Rules]
            ENV_VARS[Environment Variables]
            SECRET_MANAGEMENT[Secret Management]
        end
    end

    JWT_STORAGE --> TOKEN_REFRESH
    TOKEN_REFRESH --> ROUTE_GUARDS

    ROUTE_GUARDS --> CORS_POLICY
    CORS_POLICY --> RATE_LIMITING
    RATE_LIMITING --> JWT_AUTH
    JWT_AUTH --> PERMISSION_CLASSES

    PERMISSION_CLASSES --> PASSWORD_HASHING
    PASSWORD_HASHING --> DATA_ENCRYPTION
    DATA_ENCRYPTION --> SQL_INJECTION
    SQL_INJECTION --> XSS_PROTECTION

    XSS_PROTECTION --> HTTPS
    HTTPS --> FIREWALL
    FIREWALL --> ENV_VARS
    ENV_VARS --> SECRET_MANAGEMENT

    style JWT_AUTH fill:#ff4444
    style HTTPS fill:#00aa00
```

## 7. Performance & Scalability

### 7.1. Caching Strategy

```mermaid
graph TB
    subgraph "Multi-Level Caching"
        subgraph "Frontend Cache"
            BROWSER_CACHE[Browser Cache]
            REACT_QUERY_CACHE[React Query Cache]
            REDUX_CACHE[Redux Store Cache]
        end

        subgraph "API Cache"
            REDIS_API_CACHE[Redis API Cache]
            REDIS_SESSION[Redis Session Cache]
            REDIS_TASK[Redis Task Cache]
        end

        subgraph "Database Cache"
            DB_QUERY_CACHE[Database Query Cache]
            DB_CONNECTION_POOL[Connection Pooling]
        end

        subgraph "CDN Cache"
            STATIC_CACHE[Static Assets Cache]
            IMAGE_CACHE[Image Cache]
            VIDEO_CACHE[Video Cache]
        end
    end

    BROWSER_CACHE --> REACT_QUERY_CACHE
    REACT_QUERY_CACHE --> REDUX_CACHE

    REDUX_CACHE --> REDIS_API_CACHE
    REDIS_API_CACHE --> REDIS_SESSION
    REDIS_SESSION --> REDIS_TASK

    REDIS_TASK --> DB_QUERY_CACHE
    DB_QUERY_CACHE --> DB_CONNECTION_POOL

    DB_CONNECTION_POOL --> STATIC_CACHE
    STATIC_CACHE --> IMAGE_CACHE
    IMAGE_CACHE --> VIDEO_CACHE

    style REDIS_API_CACHE fill:#dc382d
    style STATIC_CACHE fill:#ff6b35
```

### 7.2. Background Processing

```mermaid
graph TB
    subgraph "Celery Task Architecture"
        subgraph "Task Producers"
            DJANGO_VIEWS[Django Views]
            SCHEDULER[Celery Beat Scheduler]
            MANUAL_TRIGGER[Manual Triggers]
        end

        subgraph "Message Broker"
            REDIS_BROKER[Redis Broker]
            TASK_QUEUE[Task Queue]
            RESULT_BACKEND[Result Backend]
        end

        subgraph "Task Workers"
            RECOMMENDATION_WORKER[Recommendation Worker]
            MOVIE_SYNC_WORKER[Movie Sync Worker]
            ANALYTICS_WORKER[Analytics Worker]
            EMAIL_WORKER[Email Worker]
        end

        subgraph "Task Types"
            RECOMMENDATION_TASKS[Recommendation Tasks]
            MOVIE_SYNC_TASKS[Movie Sync Tasks]
            ANALYTICS_TASKS[Analytics Tasks]
            NOTIFICATION_TASKS[Notification Tasks]
        end
    end

    DJANGO_VIEWS --> REDIS_BROKER
    SCHEDULER --> REDIS_BROKER
    MANUAL_TRIGGER --> REDIS_BROKER

    REDIS_BROKER --> TASK_QUEUE
    TASK_QUEUE --> RESULT_BACKEND

    TASK_QUEUE --> RECOMMENDATION_WORKER
    TASK_QUEUE --> MOVIE_SYNC_WORKER
    TASK_QUEUE --> ANALYTICS_WORKER
    TASK_QUEUE --> EMAIL_WORKER

    RECOMMENDATION_WORKER --> RECOMMENDATION_TASKS
    MOVIE_SYNC_WORKER --> MOVIE_SYNC_TASKS
    ANALYTICS_WORKER --> ANALYTICS_TASKS
    EMAIL_WORKER --> NOTIFICATION_TASKS

    style REDIS_BROKER fill:#dc382d
    style RECOMMENDATION_WORKER fill:#ff6b35
```

## 8. Monitoring & Observability

### 8.1. Logging & Monitoring

```mermaid
graph TB
    subgraph "Monitoring Stack"
        subgraph "Application Logging"
            DJANGO_LOGS[Django Logs]
            CELERY_LOGS[Celery Logs]
            API_LOGS[API Logs]
        end

        subgraph "Performance Monitoring"
            RESPONSE_TIME[Response Time]
            ERROR_RATE[Error Rate]
            THROUGHPUT[Throughput]
            MEMORY_USAGE[Memory Usage]
        end

        subgraph "Business Metrics"
            USER_REGISTRATIONS[User Registrations]
            MOVIE_VIEWS[Movie Views]
            RECOMMENDATION_CLICKS[Recommendation Clicks]
            CONVERSION_RATE[Conversion Rate]
        end

        subgraph "Infrastructure Monitoring"
            DATABASE_METRICS[Database Metrics]
            REDIS_METRICS[Redis Metrics]
            ELASTICSEARCH_METRICS[Elasticsearch Metrics]
            EXTERNAL_API_METRICS[External API Metrics]
        end
    end

    DJANGO_LOGS --> RESPONSE_TIME
    CELERY_LOGS --> ERROR_RATE
    API_LOGS --> THROUGHPUT

    RESPONSE_TIME --> USER_REGISTRATIONS
    ERROR_RATE --> MOVIE_VIEWS
    THROUGHPUT --> RECOMMENDATION_CLICKS

    USER_REGISTRATIONS --> DATABASE_METRICS
    MOVIE_VIEWS --> REDIS_METRICS
    RECOMMENDATION_CLICKS --> ELASTICSEARCH_METRICS

    DATABASE_METRICS --> EXTERNAL_API_METRICS
    REDIS_METRICS --> EXTERNAL_API_METRICS
    ELASTICSEARCH_METRICS --> EXTERNAL_API_METRICS

    style DJANGO_LOGS fill:#092e20
    style DATABASE_METRICS fill:#336791
```

## 9. Technology Stack Summary

### 9.1. Backend Stack

```
Django 4.x
├── Django REST Framework (API)
├── Django CORS Headers (CORS)
├── Django Filter (Filtering)
├── Django Redis (Caching)
├── Django Elasticsearch DSL (Search)
├── Django Celery Beat (Scheduling)
├── WhiteNoise (Static Files)
├── PostgreSQL (Database)
├── Redis Cloud (Cache & Message Broker)
├── Elasticsearch Cloud (Search)
├── Celery (Background Tasks)
├── Gunicorn (WSGI Server)
└── JWT Authentication
```

### 9.2. Frontend Stack

```
React 18.2.0
├── Redux Toolkit (State Management)
├── React Query v5 (Data Fetching)
├── React Router v6 (Routing)
├── Tailwind CSS (Styling)
├── Material-UI v7 (UI Components)
├── Framer Motion (Animations)
├── Chart.js (Charts)
├── Axios (HTTP Client)
├── PayPal React (Payments)
├── Google OAuth (Authentication)
├── React Window (Virtualization)
├── Swiper (Carousel)
└── TypeScript (Type Safety)
```

### 9.3. DevOps & Deployment

```
Render.com (Hosting)
├── PostgreSQL Database
├── Redis Cloud
├── Elasticsearch Cloud
├── Automatic SSL
├── CDN Integration
└── Environment Variables

Vercel (Frontend)
├── Automatic Deployments
├── Edge Functions
├── CDN Distribution
└── Performance Monitoring
```

## 10. Key Features & Capabilities

### 10.1. Core Features

- ✅ **Advanced Movie Recommendations** (Collaborative, Demographic, Hybrid)
- ✅ **Real-time Search** (Elasticsearch)
- ✅ **User Authentication** (JWT + Google OAuth)
- ✅ **Movie Reviews & Ratings** (with Spoiler Detection)
- ✅ **Subscription Management** (PayPal Integration)
- ✅ **Admin & Moderator Dashboards**
- ✅ **Real-time Analytics**
- ✅ **Background Task Processing**
- ✅ **Multi-language Support**
- ✅ **Responsive Design**

### 10.2. Performance Features

- ✅ **Multi-level Caching** (Redis + Browser + CDN)
- ✅ **Database Optimization** (Indexing + Connection Pooling)
- ✅ **Background Processing** (Celery Workers)
- ✅ **Static File Optimization** (WhiteNoise + CDN)
- ✅ **API Response Caching**
- ✅ **Lazy Loading & Virtualization**
- ✅ **Image Optimization**

### 10.3. Security Features

- ✅ **JWT Authentication**
- ✅ **CORS Protection**
- ✅ **Rate Limiting**
- ✅ **Input Validation**
- ✅ **SQL Injection Prevention**
- ✅ **XSS Protection**
- ✅ **HTTPS/SSL**
- ✅ **Environment Variable Management**

This architecture provides a robust, scalable, and maintainable foundation for the Movie Recommendation System with modern best practices and technologies.
