# Kiến Trúc Hệ Thống Movie Recommendation

## 1. Kiến Trúc Tổng Thể

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React App] --> B[Redux Store]
        A --> C[React Query Cache]
        A --> D[Local Storage]
    end

    subgraph "API Gateway"
        E[Nginx Load Balancer] --> F[Django REST API]
        F --> G[Authentication Service]
        F --> H[Rate Limiting]
    end

    subgraph "Backend Services"
        I[Movie Service] --> J[User Service]
        I --> K[Recommendation Engine]
        I --> L[Search Service]
    end

    subgraph "Data Layer"
        M[PostgreSQL Database] --> N[Redis Cache]
        M --> O[Elasticsearch]
        M --> P[File Storage]
    end

    subgraph "Performance Layer"
        Q[Database Indexes] --> M
        R[Query Optimization] --> I
        S[Caching Strategy] --> N
        T[CDN] --> P
    end

    A --> E
    E --> I
    I --> M
    N --> I
```

## 2. Kiến Trúc Performance Optimization

```mermaid
graph LR
    subgraph "Frontend Optimization"
        A1[Infinite Scroll] --> A2[Image Preloading]
        A2 --> A3[Debounced Search]
        A3 --> A4[Memory Management]
    end

    subgraph "API Optimization"
        B1[Query Optimization] --> B2[Response Caching]
        B2 --> B3[Connection Pooling]
        B3 --> B4[Rate Limiting]
    end

    subgraph "Database Optimization"
        C1[Strategic Indexing] --> C2[Denormalization]
        C2 --> C3[Query Planning]
        C3 --> C4[Partitioning]
    end

    subgraph "Cache Strategy"
        D1[Redis Cache] --> D2[CDN Cache]
        D2 --> D3[Browser Cache]
        D3 --> D4[Application Cache]
    end

    A1 --> B1
    B1 --> C1
    C1 --> D1
```

## 3. Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Gateway
    participant C as Cache Layer
    participant D as Database
    participant S as Search Engine

    U->>F: Search Request
    F->>A: API Call
    A->>C: Check Cache

    alt Cache Hit
        C->>A: Return Cached Data
        A->>F: Response
        F->>U: Display Results
    else Cache Miss
        A->>D: Database Query
        D->>A: Query Results
        A->>C: Store in Cache
        A->>F: Response
        F->>U: Display Results
    end

    Note over F,U: Infinite Scroll
    F->>A: Next Page Request
    A->>D: Paginated Query
    D->>A: Next Page Data
    A->>F: Paginated Response
    F->>U: Append Results
```

## 4. Performance Optimization Flow

```mermaid
flowchart TD
    A[User Request] --> B{Check Cache}
    B -->|Hit| C[Return Cached Data]
    B -->|Miss| D[Database Query]

    D --> E{Use Optimized Query?}
    E -->|Yes| F[Optimized Query Path]
    E -->|No| G[Standard Query Path]

    F --> H[Use Indexes]
    H --> I[Apply Filters]
    I --> J[Limit Results]
    J --> K[Cache Results]

    G --> L[Full Table Scan]
    L --> M[Apply Filters]
    M --> N[Sort Results]
    N --> O[Cache Results]

    K --> P[Return Response]
    O --> P
    C --> P

    P --> Q[Frontend Processing]
    Q --> R[Infinite Scroll]
    R --> S[Image Optimization]
    S --> T[Display Results]
```

## 5. Database Schema Optimization

```mermaid
erDiagram
    MOVIE {
        int id PK
        string title_en
        string title_vi
        date release_date
        string poster_url
        decimal cached_imdb_rating
        decimal cached_tmdb_rating
        decimal combined_rating_score
        boolean is_popular
        boolean is_top_rated
        boolean is_upcoming
        int runtime
        boolean is_adult
        string status
    }

    MOVIE_GENRE {
        int id PK
        int movie_id FK
        int genre_id FK
    }

    GENRE {
        int id PK
        string name
        string description
    }

    MOVIE_RATING {
        int id PK
        int movie_id FK
        decimal imdb_rating
        int imdb_votes
        decimal tmdb_rating
        int tmdb_votes
    }

    MOVIE ||--o{ MOVIE_GENRE : has
    MOVIE ||--o{ MOVIE_RATING : has
    GENRE ||--o{ MOVIE_GENRE : belongs_to
```

## 6. Cache Strategy Diagram

```mermaid
graph TD
    subgraph "Cache Layers"
        A[Browser Cache] --> B[CDN Cache]
        B --> C[Application Cache]
        C --> D[Database Cache]
    end

    subgraph "Cache Types"
        E[Search Results] --> F[10 minutes]
        G[Featured Movies] --> H[5 minutes]
        I[Movie Details] --> J[10 minutes]
        K[User Data] --> L[30 minutes]
    end

    subgraph "Cache Invalidation"
        M[Time-based] --> N[Event-based]
        N --> O[Manual Clear]
    end

    A --> E
    B --> G
    C --> I
    D --> K
```

## 7. Performance Metrics Dashboard

```mermaid
graph LR
    subgraph "Response Time"
        A1[< 500ms] --> A2[Excellent]
        A3[500ms-1s] --> A4[Good]
        A5[1s-2s] --> A6[Acceptable]
        A7[> 2s] --> A8[Needs Optimization]
    end

    subgraph "Cache Hit Rate"
        B1[> 80%] --> B2[Excellent]
        B3[60-80%] --> B4[Good]
        B5[40-60%] --> B6[Acceptable]
        B7[< 40%] --> B8[Needs Improvement]
    end

    subgraph "Database Queries"
        C1[1-5 queries] --> C2[Optimized]
        C3[5-10 queries] --> C4[Good]
        C5[10-20 queries] --> C6[Acceptable]
        C7[> 20 queries] --> C8[Needs Optimization]
    end

    subgraph "Memory Usage"
        D1[< 100MB] --> D2[Excellent]
        D3[100-200MB] --> D4[Good]
        D5[200-500MB] --> D6[Acceptable]
        D7[> 500MB] --> D8[Needs Optimization]
    end
```
