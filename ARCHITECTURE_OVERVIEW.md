# Kiến Trúc Tổng Quan Website Movie Recommendation System

## 1. Sơ Đồ Kiến Trúc Tổng Quan (Đã Sắp Xếp Lại)

```mermaid
graph TB
    subgraph "Tầng Người Dùng"
        WEB[🌐 Trình Duyệt Web]
        MOB[📱 Trình Duyệt Mobile]
    end

    subgraph "Tầng Giao Diện (React.js)"
        REACT[⚛️ React.js 18.x]
        REDUX[🔄 Redux Toolkit]
        RQ[📡 React Query]
        ROUTER[🛣️ React Router]
        TAILWIND[🎨 Tailwind CSS]
    end

    subgraph "Tầng Dịch Vụ Backend (Django)"
        DJANGO[🐍 Django 4.x REST API]
        CELERY[⚙️ Celery Workers]
        GUNICORN[🦄 Gunicorn WSGI]
    end

    subgraph "Tầng Dữ Liệu"
        POSTGRES[(🗄️ PostgreSQL 15)]
        REDIS[(⚡ Redis 7.0)]
        ELASTIC[(🔍 Elasticsearch)]
    end

    subgraph "Dịch Vụ Bên Ngoài"
        TMDB[🎬 TMDB API]
        IMDB[📊 IMDB Dataset]
        PAYPAL[💳 PayPal API]
        GOOGLE[🔐 Google OAuth]
        EMAIL[📧 Email Service]
    end

    subgraph "Triển Khai (Render.com)"
        RENDER[☁️ Render Cloud]
        STATIC[📁 Static Files]
    end

    %% Tầng Người Dùng đến Giao Diện
    WEB -->|"Gửi Yêu Cầu HTTP"| REACT
    MOB -->|"Gửi Yêu Cầu HTTP"| REACT

    %% Tầng Giao Diện Nội Bộ
    REACT -->|"Quản Lý Trạng Thái"| REDUX
    REACT -->|"Lấy Dữ Liệu"| RQ
    REACT -->|"Điều Hướng"| ROUTER
    REACT -->|"Tạo Kiểu"| TAILWIND

    %% Giao Diện đến Backend
    REACT -->|"Gọi API (Axios)"| DJANGO

    %% Backend Nội Bộ
    DJANGO -->|"Máy Chủ WSGI"| GUNICORN
    DJANGO -->|"Xử Lý Tác Vụ Nền"| CELERY

    %% Backend đến Dữ Liệu
    DJANGO -->|"Thao Tác CRUD"| POSTGRES
    DJANGO -->|"Đọc/Ghi Cache"| REDIS
    DJANGO -->|"Truy Vấn Tìm Kiếm"| ELASTIC

    %% Backend đến Dịch Vụ Bên Ngoài
    DJANGO -->|"Lấy Dữ Liệu Phim"| TMDB
    DJANGO -->|"Import Dataset"| IMDB
    DJANGO -->|"Xử Lý Thanh Toán"| PAYPAL
    DJANGO -->|"Xác Thực OAuth"| GOOGLE
    DJANGO -->|"Gửi Email"| EMAIL

    %% Triển Khai
    DJANGO -->|"Triển Khai"| RENDER
    RENDER -->|"Phục Vụ"| STATIC

    style REACT fill:#61dafb
    style DJANGO fill:#092e20
    style POSTGRES fill:#336791
    style REDIS fill:#dc382d
    style ELASTIC fill:#f7df1e
    style RENDER fill:#00d4aa
```

## 2. Cấu Trúc Ứng Dụng Chi Tiết

```mermaid
graph LR
    subgraph "Giao Diện (React.js)"
        UI[Thành Phần UI]
        STATE[Redux Store]
        API[Axios Client]
        ROUTES[React Router]
    end

    subgraph "Backend (Django Apps)"
        MOVIES[Ứng Dụng Phim]
        USERS[Ứng Dụng Người Dùng]
        RECS[Ứng Dụng Gợi Ý]
        METADATA[Ứng Dụng Metadata]
        SUBSCRIPTIONS[Ứng Dụng Đăng Ký]
        API_REST[REST API]
    end

    subgraph "Cơ Sở Dữ Liệu & Cache"
        DB[(PostgreSQL)]
        CACHE[(Redis)]
        SEARCH[(Elasticsearch)]
    end

    subgraph "Tác Vụ Nền"
        CELERY_WORKER[Celery Worker]
        CELERY_BEAT[Celery Beat]
        FLOWER[Flower Monitor]
    end

    UI -->|"Gửi Hành Động"| STATE
    STATE -->|"Cập Nhật Trạng Thái"| UI
    UI -->|"Yêu Cầu API"| API
    API -->|"Gọi HTTP"| API_REST
    UI -->|"Điều Hướng"| ROUTES

    API_REST -->|"Xử Lý Yêu Cầu"| MOVIES
    API_REST -->|"Xử Lý Yêu Cầu"| USERS
    API_REST -->|"Xử Lý Yêu Cầu"| RECS
    API_REST -->|"Xử Lý Yêu Cầu"| METADATA
    API_REST -->|"Xử Lý Yêu Cầu"| SUBSCRIPTIONS

    MOVIES -->|"Thao Tác CRUD"| DB
    USERS -->|"Thao Tác CRUD"| DB
    RECS -->|"Thao Tác CRUD"| DB
    METADATA -->|"Thao Tác CRUD"| DB
    SUBSCRIPTIONS -->|"Thao Tác CRUD"| DB

    MOVIES -->|"Lưu Cache"| CACHE
    USERS -->|"Lưu Phiên Làm Việc"| CACHE
    RECS -->|"Lưu Kết Quả"| CACHE

    MOVIES -->|"Đánh Chỉ Mục Nội Dung"| SEARCH
    RECS -->|"Truy Vấn Tìm Kiếm"| SEARCH

    MOVIES -->|"Xử Lý Tác Vụ"| CELERY_WORKER
    USERS -->|"Xử Lý Tác Vụ"| CELERY_WORKER
    RECS -->|"Xử Lý Tác Vụ"| CELERY_WORKER
    CELERY_WORKER -->|"Lên Lịch Tác Vụ"| CELERY_BEAT
    CELERY_WORKER -->|"Giám Sát Tác Vụ"| FLOWER

    style UI fill:#61dafb
    style MOVIES fill:#ff6b35
    style USERS fill:#4ecdc4
    style RECS fill:#45b7d1
    style CELERY_WORKER fill:#ffa726
```

## 3. Luồng Dữ Liệu Thực Tế

```mermaid
sequenceDiagram
    participant U as Người Dùng
    participant F as React Frontend
    participant A as Django API
    participant D as PostgreSQL
    participant C as Redis Cache
    participant E as API Bên Ngoài
    participant B as Tác Vụ Celery

    U->>F: Truy cập website
    F->>A: Yêu cầu API (Axios)
    A->>C: Kiểm tra cache
    alt Cache có sẵn
        C->>A: Trả về dữ liệu cache
    else Cache không có
        A->>D: Truy vấn cơ sở dữ liệu
        D->>A: Trả về dữ liệu
        A->>C: Lưu vào cache
    end
    A->>E: Lấy dữ liệu bên ngoài (nếu cần)
    E->>A: Trả về dữ liệu bên ngoài
    A->>B: Kích hoạt tác vụ nền
    B->>D: Xử lý dữ liệu
    A->>F: Phản hồi API
    F->>U: Hiển thị nội dung
```

## 4. Technology Stack (Đã Kiểm Tra Lại)

### Frontend

- **React.js 18.x** - UI Framework
- **Redux Toolkit** - State Management
- **React Query** - Data Fetching & Caching
- **React Router** - Client-side Routing
- **Tailwind CSS** - Utility-first CSS
- **Axios** - HTTP Client
- **Framer Motion** - Animations
- **i18next** - Internationalization

### Backend

- **Django 4.x** - Web Framework
- **Django REST Framework** - API Framework
- **PostgreSQL 15** - Primary Database
- **Redis 7.0** - Cache & Message Broker
- **Elasticsearch** - Search Engine
- **Celery** - Background Task Processing
- **Gunicorn** - WSGI Server

### Infrastructure & Deployment

- **Render.com** - Cloud Platform
- **Docker & Docker Compose** - Containerization
- **Gunicorn** - Production WSGI Server

### External Services

- **TMDB API** - Movie Data Source
- **IMDB Dataset** - Movie Ratings & Metadata
- **PayPal API** - Payment Processing
- **Google OAuth** - Authentication
- **Email Service** - SMTP/SendGrid

## 5. Cấu Trúc Database (PostgreSQL)

```mermaid
graph TB
    subgraph "Bảng Cốt Lõi"
        MOVIES[Bảng Phim]
        USERS[Bảng Người Dùng]
        GENRES[Bảng Thể Loại]
    end

    subgraph "Liên Quan Đến Phim"
        MOVIE_METADATA[Metadata Phim]
        MOVIE_CAST[Diễn Viên Phim]
        MOVIE_REVIEWS[Đánh Giá Phim]
        MOVIE_RATINGS[Điểm Số Phim]
        MOVIE_TRAILERS[Trailer Phim]
    end

    subgraph "Liên Quan Đến Người Dùng"
        USER_PREFERENCES[Sở Thích Người Dùng]
        USER_FAVORITES[Phim Yêu Thích]
        WATCHLISTS[Danh Sách Xem]
        SEARCH_HISTORY[Lịch Sử Tìm Kiếm]
    end

    subgraph "Hệ Thống Gợi Ý"
        USER_SIMILARITY[Độ Tương Đồng Người Dùng]
        MOVIE_SIMILARITY[Độ Tương Đồng Phim]
        RECOMMENDATION_RESULTS[Kết Quả Gợi Ý]
        DEMOGRAPHIC_CLUSTERS[Cụm Nhân Khẩu Học]
    end

    subgraph "Quản Trị & Phân Tích"
        MOVIE_ADMIN_CONTROL[Kiểm Soát Admin Phim]
        MOVIE_QUALITY_METRICS[Chỉ Số Chất Lượng Phim]
        USER_INTERACTIONS[Tương Tác Người Dùng]
        PRODUCTION_METRICS[Chỉ Số Sản Xuất]
    end

    MOVIES -->|"Có Metadata"| MOVIE_METADATA
    MOVIES -->|"Có Diễn Viên"| MOVIE_CAST
    MOVIES -->|"Có Đánh Giá"| MOVIE_REVIEWS
    MOVIES -->|"Có Điểm Số"| MOVIE_RATINGS
    MOVIES -->|"Có Trailer"| MOVIE_TRAILERS

    USERS -->|"Có Sở Thích"| USER_PREFERENCES
    USERS -->|"Có Phim Yêu Thích"| USER_FAVORITES
    USERS -->|"Có Danh Sách Xem"| WATCHLISTS
    USERS -->|"Có Lịch Sử Tìm Kiếm"| SEARCH_HISTORY

    USERS -->|"Tương Đồng Với"| USER_SIMILARITY
    MOVIES -->|"Tương Đồng Với"| MOVIE_SIMILARITY
    USERS -->|"Nhận Gợi Ý"| RECOMMENDATION_RESULTS
    USERS -->|"Thuộc Cụm"| DEMOGRAPHIC_CLUSTERS

    MOVIES -->|"Có Kiểm Soát Admin"| MOVIE_ADMIN_CONTROL
    MOVIES -->|"Có Chỉ Số Chất Lượng"| MOVIE_QUALITY_METRICS
    MOVIES -->|"Theo Dõi Tương Tác"| USER_INTERACTIONS
    MOVIES -->|"Có Chỉ Số Sản Xuất"| PRODUCTION_METRICS

    style MOVIES fill:#ff6b35
    style USERS fill:#4ecdc4
    style RECOMMENDATION_RESULTS fill:#45b7d1
```

## 6. Tính Năng Chính

### 🎬 Movie Management

- Database phim toàn diện (2,400+ dòng code models)
- Hỗ trợ đa ngôn ngữ (Anh/Việt)
- Hệ thống đánh giá & review phức tạp
- Quản lý cast, crew, trailer, images
- Quality metrics & content moderation

### 👥 User Management

- JWT Authentication & Authorization
- Profile management với demographics
- Watchlist & favorites system
- Email verification system
- Subscription management

### 🧠 Recommendation System

- Collaborative filtering algorithms
- Content-based filtering
- Demographic filtering
- Hybrid recommendation algorithms
- Real-time recommendation generation

### 🛠️ Admin & Moderation

- Admin dashboard cho content management
- Moderator dashboard cho review moderation
- Content quality assessment
- Automated spoiler detection
- User interaction analytics

### ⚡ Performance & Scalability

- Redis caching cho improved performance
- Elasticsearch cho fast search
- Database optimization với indexing
- Background task processing với Celery
- Cloud deployment trên Render.com

## 7. Deployment Architecture

```mermaid
graph TB
    subgraph "Nền Tảng Cloud Render.com"
        subgraph "Dịch Vụ Web"
            DJANGO_APP[Ứng Dụng Django]
            GUNICORN[Máy Chủ Gunicorn]
        end

        subgraph "Cơ Sở Dữ Liệu"
            POSTGRES_CLOUD[(PostgreSQL)]
        end

        subgraph "Cache & Tìm Kiếm"
            REDIS_CLOUD[(Redis)]
            ELASTIC_CLOUD[(Elasticsearch)]
        end

        subgraph "Tác Vụ Nền"
            CELERY_CLOUD[Celery Workers]
            FLOWER_CLOUD[Flower Monitor]
        end
    end

    subgraph "Dịch Vụ Bên Ngoài"
        TMDB_API[TMDB API]
        PAYPAL_API[PayPal API]
        GOOGLE_OAUTH[Google OAuth]
    end

    DJANGO_APP -->|"Máy Chủ WSGI"| GUNICORN
    DJANGO_APP -->|"Thao Tác CRUD"| POSTGRES_CLOUD
    DJANGO_APP -->|"Thao Tác Cache"| REDIS_CLOUD
    DJANGO_APP -->|"Thao Tác Tìm Kiếm"| ELASTIC_CLOUD
    DJANGO_APP -->|"Xử Lý Tác Vụ Nền"| CELERY_CLOUD
    CELERY_CLOUD -->|"Giám Sát Tác Vụ"| FLOWER_CLOUD

    DJANGO_APP -->|"Lấy Dữ Liệu Phim"| TMDB_API
    DJANGO_APP -->|"Xử Lý Thanh Toán"| PAYPAL_API
    DJANGO_APP -->|"Xác Thực OAuth"| GOOGLE_OAUTH

    style DJANGO_APP fill:#092e20
    style POSTGRES_CLOUD fill:#336791
    style REDIS_CLOUD fill:#dc382d
    style ELASTIC_CLOUD fill:#f7df1e
```

## 8. Luồng Tương Tác Chi Tiết

```mermaid
graph TB
    subgraph "Hành Động Người Dùng"
        LOGIN[Đăng Nhập]
        BROWSE[Duyệt Phim]
        SEARCH[Tìm Kiếm Phim]
        RATE[Đánh Giá Phim]
        REVIEW[Viết Đánh Giá]
        FAVORITE[Thêm Vào Yêu Thích]
    end

    subgraph "Xử Lý Giao Diện"
        AUTH[Xác Thực]
        STATE[Quản Lý Trạng Thái]
        API_CALLS[Gọi API]
        UI_UPDATE[Cập Nhật Giao Diện]
    end

    subgraph "Xử Lý Backend"
        API_HANDLE[Xử Lý API]
        BUSINESS_LOGIC[Logic Nghiệp Vụ]
        DATA_ACCESS[Truy Cập Dữ Liệu]
        CACHE_MANAGE[Quản Lý Cache]
    end

    subgraph "Thao Tác Dữ Liệu"
        DB_READ[Đọc Database]
        DB_WRITE[Ghi Database]
        CACHE_READ[Đọc Cache]
        CACHE_WRITE[Ghi Cache]
        SEARCH_QUERY[Truy Vấn Tìm Kiếm]
    end

    LOGIN -->|"Token JWT"| AUTH
    BROWSE -->|"Lấy Dữ Liệu"| API_CALLS
    SEARCH -->|"Yêu Cầu Tìm Kiếm"| API_CALLS
    RATE -->|"Dữ Liệu Đánh Giá"| API_CALLS
    REVIEW -->|"Nội Dung Đánh Giá"| API_CALLS
    FAVORITE -->|"Hành Động Yêu Thích"| API_CALLS

    AUTH -->|"Xác Thực Token"| API_HANDLE
    API_CALLS -->|"Yêu Cầu HTTP"| API_HANDLE
    API_HANDLE -->|"Xử Lý Yêu Cầu"| BUSINESS_LOGIC
    BUSINESS_LOGIC -->|"Thao Tác Dữ Liệu"| DATA_ACCESS
    DATA_ACCESS -->|"Kiểm Tra Cache"| CACHE_MANAGE

    CACHE_MANAGE -->|"Cache Không Có"| DB_READ
    CACHE_MANAGE -->|"Cache Có Sẵn"| CACHE_READ
    BUSINESS_LOGIC -->|"Cập Nhật Dữ Liệu"| DB_WRITE
    BUSINESS_LOGIC -->|"Lưu Cache"| CACHE_WRITE
    BUSINESS_LOGIC -->|"Tìm Kiếm Dữ Liệu"| SEARCH_QUERY

    DB_READ -->|"Trả Về Dữ Liệu"| BUSINESS_LOGIC
    CACHE_READ -->|"Trả Về Dữ Liệu"| BUSINESS_LOGIC
    DB_WRITE -->|"Xác Nhận Cập Nhật"| BUSINESS_LOGIC
    CACHE_WRITE -->|"Xác Nhận Cache"| BUSINESS_LOGIC
    SEARCH_QUERY -->|"Trả Về Kết Quả"| BUSINESS_LOGIC

    BUSINESS_LOGIC -->|"Phản Hồi API"| API_HANDLE
    API_HANDLE -->|"Phản Hồi HTTP"| API_CALLS
    API_CALLS -->|"Cập Nhật Trạng Thái"| STATE
    STATE -->|"Hiển Thị Giao Diện"| UI_UPDATE

    style LOGIN fill:#4ecdc4
    style API_CALLS fill:#61dafb
    style BUSINESS_LOGIC fill:#ff6b35
    style DB_READ fill:#336791
    style CACHE_READ fill:#dc382d
```

---

_Kiến trúc tổng quan đã được sắp xếp lại và chuyển đổi các action sang tiếng Việt để dễ hiểu hơn._
