# 2.2. CƠ SỞ LÝ THUYẾT

## 2.2.1. Django REST Framework (DRF)

### a. Định nghĩa và Tổng quan

Django REST Framework là một bộ công cụ mạnh mẽ và linh hoạt được xây dựng trên nền tảng Django framework, được thiết kế đặc biệt để phát triển các Web API. DRF cung cấp một cách tiếp cận có cấu trúc và hiệu quả để xây dựng các RESTful API, cho phép các nhà phát triển tạo ra các endpoint API một cách nhanh chóng và có tổ chức.

DRF được phát triển với mục tiêu chính là đơn giản hóa quá trình tạo ra các API web, đồng thời duy trì tính linh hoạt và khả năng mở rộng. Framework này tuân thủ các nguyên tắc REST (Representational State Transfer), đảm bảo rằng các API được tạo ra có cấu trúc rõ ràng, dễ hiểu và dễ sử dụng.

### b. Kiến trúc và Thành phần chính

#### b.1. Django Object Relational Mapper (ORM)

Django ORM là một lớp trừu tượng hóa cơ sở dữ liệu, cho phép các nhà phát triển tương tác với cơ sở dữ liệu thông qua các đối tượng Python thay vì phải viết các câu lệnh SQL trực tiếp. ORM cung cấp:

- **Model Definition**: Định nghĩa cấu trúc dữ liệu thông qua các class Python
- **Query API**: Cung cấp các phương thức truy vấn dữ liệu mạnh mẽ và linh hoạt
- **Database Migration**: Quản lý các thay đổi schema cơ sở dữ liệu một cách tự động
- **Relationship Management**: Xử lý các mối quan hệ giữa các bảng dữ liệu

#### b.2. Serializers

Serializers trong DRF đóng vai trò quan trọng trong việc chuyển đổi dữ liệu giữa các định dạng khác nhau:

- **Model Serializers**: Tự động tạo serializer dựa trên Django models
- **Custom Serializers**: Cho phép tùy chỉnh logic serialization
- **Validation**: Cung cấp hệ thống validation mạnh mẽ
- **Nested Serialization**: Hỗ trợ serialization các đối tượng phức tạp

#### b.3. ViewSets và API Views

DRF cung cấp các lớp view chuyên biệt cho API:

- **APIView**: Lớp cơ bản cho việc tạo API endpoints
- **ViewSets**: Tự động tạo CRUD operations cho models
- **Generic Views**: Cung cấp các view được tối ưu hóa cho các tác vụ phổ biến
- **Mixins**: Cho phép tái sử dụng logic giữa các views

### c. Tính năng nâng cao

#### c.1. Authentication và Permissions

DRF cung cấp hệ thống xác thực và phân quyền toàn diện:

- **Session Authentication**: Xác thực dựa trên session
- **Token Authentication**: Xác thực dựa trên token
- **OAuth2**: Hỗ trợ OAuth2 authentication
- **Custom Permissions**: Cho phép tạo quyền tùy chỉnh

#### c.2. Throttling và Rate Limiting

- **User-based Throttling**: Giới hạn request theo user
- **Scope-based Throttling**: Giới hạn request theo phạm vi
- **Custom Throttling**: Tạo logic giới hạn tùy chỉnh

#### c.3. Pagination

- **PageNumberPagination**: Phân trang theo số trang
- **LimitOffsetPagination**: Phân trang theo limit/offset
- **CursorPagination**: Phân trang theo cursor

### d. Lợi ích và Ưu điểm

#### d.1. Hiệu quả phát triển

- **Rapid Development**: Phát triển nhanh chóng với các công cụ có sẵn
- **Code Reusability**: Tái sử dụng code cao với các component có sẵn
- **Consistency**: Đảm bảo tính nhất quán trong cấu trúc API

#### d.2. Bảo mật và Ổn định

- **Built-in Security**: Tích hợp sẵn các tính năng bảo mật
- **Input Validation**: Validation đầu vào mạnh mẽ
- **Error Handling**: Xử lý lỗi một cách có hệ thống

#### d.3. Khả năng mở rộng

- **Scalability**: Dễ dàng mở rộng khi ứng dụng phát triển
- **Modularity**: Kiến trúc module hóa, dễ bảo trì
- **Integration**: Tích hợp dễ dàng với các hệ thống khác

## 2.2.2. PostgreSQL Database

### a. Định nghĩa và Đặc điểm

PostgreSQL là một hệ quản trị cơ sở dữ liệu quan hệ (RDBMS) mã nguồn mở, được phát triển từ dự án POSTGRES tại Đại học California, Berkeley. PostgreSQL được thiết kế để xử lý các khối lượng dữ liệu lớn với hiệu suất cao và đảm bảo tính toàn vẹn dữ liệu.

### b. Kiến trúc và Tính năng chính

#### b.1. ACID Compliance

PostgreSQL tuân thủ đầy đủ các thuộc tính ACID:

- **Atomicity**: Đảm bảo tính nguyên tử của các transaction
- **Consistency**: Duy trì tính nhất quán của dữ liệu
- **Isolation**: Cô lập các transaction để tránh xung đột
- **Durability**: Đảm bảo dữ liệu được lưu trữ bền vững

#### b.2. Advanced Data Types

PostgreSQL hỗ trợ nhiều kiểu dữ liệu phức tạp:

- **JSON/JSONB**: Lưu trữ và truy vấn dữ liệu JSON hiệu quả
- **Array**: Hỗ trợ mảng đa chiều
- **Geometric**: Xử lý dữ liệu hình học
- **Network Address**: Quản lý địa chỉ mạng
- **UUID**: Hỗ trợ UUID làm primary key

#### b.3. Concurrency Control

- **MVCC (Multi-Version Concurrency Control)**: Cho phép nhiều transaction đọc/ghi đồng thời
- **Row-level Locking**: Khóa ở mức hàng để tối ưu hiệu suất
- **Deadlock Detection**: Phát hiện và xử lý deadlock tự động

### c. Tính năng nâng cao

#### c.1. Extensibility

- **Custom Functions**: Tạo các hàm tùy chỉnh bằng PL/pgSQL, Python, C
- **Extensions**: Hỗ trợ nhiều extension mở rộng
- **Foreign Data Wrappers**: Kết nối với dữ liệu từ nguồn khác

#### c.2. Performance Optimization

- **Indexing**: Hỗ trợ nhiều loại index (B-tree, Hash, GiST, SP-GiST, GIN, BRIN)
- **Query Optimization**: Optimizer thông minh cho các truy vấn phức tạp
- **Parallel Query Execution**: Thực thi truy vấn song song

#### c.3. Replication và High Availability

- **Streaming Replication**: Replication thời gian thực
- **Logical Replication**: Replication ở mức logic
- **Failover**: Tự động chuyển đổi khi primary server lỗi

### d. Lợi ích trong dự án

#### d.1. Hiệu suất cao

- Xử lý tốt các truy vấn phức tạp
- Hỗ trợ indexing mạnh mẽ
- Tối ưu hóa query tự động

#### d.2. Tính linh hoạt

- Hỗ trợ nhiều kiểu dữ liệu
- Dễ dàng mở rộng schema
- Tích hợp tốt với các công nghệ khác

#### d.3. Độ tin cậy

- ACID compliance đầy đủ
- Backup và recovery mạnh mẽ
- Cộng đồng lớn và hỗ trợ tốt

## 2.2.3. Redis Cache và Message Broker

### a. Định nghĩa và Tổng quan

Redis (Remote Dictionary Server) là một hệ thống lưu trữ dữ liệu in-memory, mã nguồn mở, được sử dụng như database, cache và message broker. Redis được thiết kế để cung cấp hiệu suất cao với tốc độ truy cập cực kỳ nhanh do lưu trữ dữ liệu trong RAM.

### b. Kiến trúc và Cấu trúc dữ liệu

#### b.1. In-Memory Storage

- **RAM-based Storage**: Dữ liệu được lưu trữ trong RAM
- **Persistence Options**: Hỗ trợ lưu trữ xuống đĩa (RDB, AOF)
- **Memory Management**: Quản lý bộ nhớ hiệu quả

#### b.2. Data Structures

Redis hỗ trợ nhiều cấu trúc dữ liệu:

- **Strings**: Lưu trữ text, binary data
- **Hashes**: Lưu trữ field-value pairs
- **Lists**: Danh sách có thứ tự
- **Sets**: Tập hợp các phần tử duy nhất
- **Sorted Sets**: Tập hợp có thứ tự với scores
- **Bitmaps**: Xử lý bit-level operations
- **HyperLogLogs**: Ước tính cardinality
- **Geospatial**: Xử lý dữ liệu địa lý

### c. Tính năng nâng cao

#### c.1. Caching Strategies

- **TTL (Time To Live)**: Tự động xóa dữ liệu hết hạn
- **LRU Eviction**: Xóa dữ liệu ít sử dụng
- **Cache Patterns**: Implement các pattern caching phổ biến

#### c.2. Pub/Sub Messaging

- **Channels**: Hệ thống kênh thông tin
- **Pattern Matching**: Subscribe theo pattern
- **Message Persistence**: Lưu trữ message khi cần

#### c.3. Transactions và Lua Scripting

- **Multi/Exec**: Thực thi nhiều lệnh atomically
- **Lua Scripts**: Thực thi logic phức tạp trên server
- **Watch/Unwatch**: Optimistic locking

### d. Ứng dụng trong dự án

#### d.1. Caching Layer

- **Database Caching**: Cache kết quả truy vấn database
- **Session Storage**: Lưu trữ session người dùng
- **API Response Caching**: Cache response của API

#### d.2. Message Queue

- **Task Queue**: Queue cho background tasks
- **Event Processing**: Xử lý các sự kiện hệ thống
- **Real-time Notifications**: Thông báo thời gian thực

#### d.3. Performance Optimization

- **Rate Limiting**: Giới hạn số request
- **Lock Management**: Quản lý distributed locks
- **Counter Management**: Quản lý các bộ đếm

## 2.2.4. Elasticsearch Search Engine

### a. Định nghĩa và Kiến trúc

Elasticsearch là một search engine phân tán, được xây dựng trên Apache Lucene, cung cấp khả năng tìm kiếm và phân tích dữ liệu thời gian thực với hiệu suất cao. Elasticsearch được thiết kế để xử lý các khối lượng dữ liệu lớn và cung cấp khả năng tìm kiếm phức tạp.

### b. Kiến trúc phân tán

#### b.1. Cluster Architecture

- **Nodes**: Các server trong cluster
- **Master Node**: Quản lý cluster metadata
- **Data Nodes**: Lưu trữ và xử lý dữ liệu
- **Client Nodes**: Xử lý client requests

#### b.2. Index và Sharding

- **Indices**: Tương đương với database trong RDBMS
- **Shards**: Phân chia dữ liệu thành các phần nhỏ
- **Replicas**: Bản sao dữ liệu để đảm bảo tính sẵn sàng

### c. Tính năng tìm kiếm

#### c.1. Full-text Search

- **Text Analysis**: Phân tích và xử lý text
- **Scoring**: Tính điểm relevance cho kết quả
- **Fuzzy Matching**: Tìm kiếm mờ
- **Wildcard Queries**: Tìm kiếm với wildcard

#### c.2. Aggregations

- **Metrics Aggregations**: Tính toán các chỉ số thống kê
- **Bucket Aggregations**: Nhóm dữ liệu theo tiêu chí
- **Pipeline Aggregations**: Xử lý kết quả aggregation

#### c.3. Mapping và Analysis

- **Field Mapping**: Định nghĩa cấu trúc dữ liệu
- **Analyzers**: Xử lý và chuẩn hóa text
- **Tokenizers**: Tách text thành tokens
- **Filters**: Lọc và xử lý tokens

### d. Ứng dụng trong dự án

#### d.1. Movie Search

- **Full-text Search**: Tìm kiếm phim theo tên, mô tả
- **Filtering**: Lọc theo genre, năm, rating
- **Sorting**: Sắp xếp theo các tiêu chí khác nhau
- **Suggestions**: Gợi ý tìm kiếm

#### d.2. Analytics và Reporting

- **User Behavior Analysis**: Phân tích hành vi người dùng
- **Trend Analysis**: Phân tích xu hướng
- **Performance Metrics**: Đo lường hiệu suất hệ thống

## 2.2.5. Celery Distributed Task Queue

### a. Định nghĩa và Mục đích

Celery là một distributed task queue system được viết bằng Python, cho phép thực hiện các tác vụ nặng trong background, tách biệt khỏi web request. Celery sử dụng message broker để giao tiếp giữa các worker processes, đảm bảo hiệu suất và khả năng mở rộng của hệ thống.

### b. Kiến trúc hệ thống

#### b.1. Core Components

- **Broker**: Message broker (Redis, RabbitMQ)
- **Workers**: Các process thực thi tasks
- **Beat**: Scheduler cho periodic tasks
- **Backend**: Lưu trữ kết quả tasks

#### b.2. Task Execution Flow

1. **Task Creation**: Tạo task và gửi đến broker
2. **Task Distribution**: Broker phân phối task đến workers
3. **Task Execution**: Workers thực thi task
4. **Result Storage**: Lưu trữ kết quả vào backend

### c. Tính năng nâng cao

#### c.1. Task Management

- **Task Routing**: Định tuyến task đến workers cụ thể
- **Task Priority**: Ưu tiên thực thi tasks
- **Task Retry**: Tự động thử lại khi task thất bại
- **Task Revocation**: Hủy bỏ task đang chạy

#### c.2. Monitoring và Control

- **Flower**: Web-based monitoring tool
- **Task States**: Theo dõi trạng thái tasks
- **Worker Management**: Quản lý workers
- **Performance Metrics**: Đo lường hiệu suất

#### c.3. Scheduling

- **Periodic Tasks**: Tasks chạy định kỳ
- **Crontab-like Scheduling**: Lên lịch theo cron format
- **Dynamic Scheduling**: Lên lịch động

### d. Ứng dụng trong dự án

#### d.1. Recommendation Generation

- **Background Processing**: Tạo recommendation trong background
- **Batch Processing**: Xử lý hàng loạt dữ liệu
- **Async Operations**: Thực hiện các tác vụ bất đồng bộ

#### d.2. Data Processing

- **Data Import**: Import dữ liệu từ external sources
- **Data Synchronization**: Đồng bộ dữ liệu
- **Report Generation**: Tạo báo cáo

## 2.2.6. ReactJS Frontend Framework

### a. Định nghĩa và Triết lý

ReactJS là một thư viện JavaScript được phát triển bởi Facebook, được thiết kế để xây dựng user interfaces một cách hiệu quả và có thể tái sử dụng. ReactJS tuân theo kiến trúc component-based, cho phép xây dựng các ứng dụng phức tạp từ các component đơn giản.

### b. Kiến trúc Component

#### b.1. Component Lifecycle

ReactJS cung cấp lifecycle methods để quản lý component:

- **Mounting Phase**: Component được tạo và thêm vào DOM

  - `constructor()`: Khởi tạo state và bind methods
  - `render()`: Render component
  - `componentDidMount()`: Component đã được mount

- **Updating Phase**: Component được cập nhật

  - `render()`: Re-render component
  - `componentDidUpdate()`: Component đã được update

- **Unmounting Phase**: Component được xóa khỏi DOM
  - `componentWillUnmount()`: Component sắp bị unmount

#### b.2. State và Props Management

- **State**: Dữ liệu nội bộ của component
- **Props**: Dữ liệu được truyền từ component cha
- **State Updates**: Cập nhật state thông qua setState()

### c. React Hooks (Modern React)

#### c.1. useState Hook

```javascript
const [state, setState] = useState(initialValue);
```

- Quản lý local state trong functional components
- Tự động re-render khi state thay đổi
- Hỗ trợ lazy initialization

#### c.2. useEffect Hook

```javascript
useEffect(() => {
  // Side effects
  return () => {
    // Cleanup
  };
}, [dependencies]);
```

- Thay thế lifecycle methods
- Xử lý side effects (API calls, subscriptions)
- Cleanup function để tránh memory leaks

#### c.3. Custom Hooks

- Tái sử dụng logic giữa các components
- Encapsulate complex logic
- Improve code organization

### d. JSX và Virtual DOM

#### d.1. JSX (JavaScript XML)

- Syntax extension cho JavaScript
- Cho phép viết HTML-like code trong JavaScript
- Compile thành JavaScript thuần

#### d.2. Virtual DOM

- In-memory representation của actual DOM
- Diffing algorithm để tối ưu updates
- Batch updates để cải thiện performance

### e. Performance Optimization

#### e.1. React.memo

- Memoize components để tránh unnecessary re-renders
- Shallow comparison của props

#### e.2. useMemo và useCallback

- Memoize expensive calculations
- Memoize functions để tránh re-creation

#### e.3. Code Splitting

- Lazy loading components
- Dynamic imports
- Route-based code splitting

## 2.2.7. Redux Toolkit State Management

### a. Định nghĩa và Mục đích

Redux Toolkit là thư viện chính thức, được khuyến nghị sử dụng để viết Redux logic. Redux Toolkit được thiết kế để giải quyết các vấn đề phổ biến khi sử dụng Redux như cấu hình phức tạp, cần nhiều package, và boilerplate code quá nhiều.

### b. Core Concepts

#### b.1. Store

- Single source of truth cho application state
- Immutable state tree
- Predictable state updates

#### b.2. Actions

- Plain objects mô tả "what happened"
- Must have `type` property
- Can contain additional data (payload)

#### b.3. Reducers

- Pure functions nhận state và action
- Return new state object
- Handle specific action types

### c. Redux Toolkit Features

#### c.1. configureStore()

```javascript
import { configureStore } from "@reduxjs/toolkit";

const store = configureStore({
  reducer: {
    movies: moviesReducer,
    users: usersReducer,
  },
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(logger),
});
```

- Tự động setup Redux DevTools
- Include default middleware
- Enable development checks

#### c.2. createSlice()

```javascript
import { createSlice } from "@reduxjs/toolkit";

const moviesSlice = createSlice({
  name: "movies",
  initialState: [],
  reducers: {
    addMovie: (state, action) => {
      state.push(action.payload);
    },
    removeMovie: (state, action) => {
      return state.filter((movie) => movie.id !== action.payload);
    },
  },
});
```

- Tự động generate action creators
- Sử dụng Immer để immutable updates
- Reduce boilerplate code

#### c.3. createAsyncThunk()

```javascript
import { createAsyncThunk } from "@reduxjs/toolkit";

export const fetchMovies = createAsyncThunk(
  "movies/fetchMovies",
  async (userId, thunkAPI) => {
    const response = await fetch(`/api/movies/${userId}`);
    return response.json();
  }
);
```

- Handle async operations
- Automatic loading states
- Error handling

### d. RTK Query

#### d.1. API Definition

```javascript
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const api = createApi({
  baseQuery: fetchBaseQuery({ baseUrl: "/api/" }),
  endpoints: (builder) => ({
    getMovies: builder.query({
      query: () => "movies",
    }),
    getMovie: builder.query({
      query: (id) => `movies/${id}`,
    }),
  }),
});
```

#### d.2. Features

- Automatic caching
- Background refetching
- Optimistic updates
- Real-time updates

### e. Benefits trong dự án

#### e.1. Centralized State Management

- Quản lý state toàn bộ ứng dụng
- Predictable state updates
- Easy debugging với Redux DevTools

#### e.2. Performance Optimization

- Selective re-rendering
- Memoized selectors
- Efficient updates

#### e.3. Developer Experience

- Less boilerplate code
- Built-in TypeScript support
- Excellent debugging tools

## 2.2.8. Machine Learning với scikit-learn

### a. Định nghĩa và Tổng quan

scikit-learn là thư viện Machine Learning mã nguồn mở cho Python, cung cấp các thuật toán học máy đơn giản và hiệu quả cho data mining và data analysis. Thư viện này được xây dựng trên NumPy, SciPy và matplotlib, cung cấp các công cụ mạnh mẽ cho việc xây dựng các hệ thống recommendation.

### b. Recommendation Algorithms

#### b.1. Collaborative Filtering

Collaborative Filtering là thuật toán đề xuất dựa trên sự tương đồng giữa người dùng hoặc items:

**User-based Collaborative Filtering:**

- Tìm người dùng có sở thích tương tự
- Đề xuất items mà người dùng tương tự đã thích
- Sử dụng similarity metrics (cosine similarity, Pearson correlation)

**Item-based Collaborative Filtering:**

- Tìm items có đặc điểm tương tự
- Đề xuất items tương tự với items đã thích
- Hiệu quả hơn với dataset lớn

#### b.2. Content-based Filtering

Đề xuất dựa trên đặc điểm và thuộc tính của items:

- **Feature Extraction**: Trích xuất đặc điểm từ items
- **User Profile**: Xây dựng profile người dùng
- **Similarity Calculation**: Tính toán độ tương đồng
- **Recommendation Generation**: Tạo danh sách đề xuất

#### b.3. Demographic Filtering

Đề xuất dựa trên thông tin nhân khẩu học:

- **Demographic Features**: Tuổi, giới tính, địa điểm
- **Clustering**: Nhóm người dùng theo đặc điểm
- **Group Preferences**: Sở thích chung của nhóm

### c. Implementation với scikit-learn

#### c.1. Data Preprocessing

```python
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer

# Feature scaling
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

# Text vectorization
vectorizer = TfidfVectorizer()
text_features = vectorizer.fit_transform(text_data)
```

#### c.2. Similarity Calculation

```python
from sklearn.metrics.pairwise import cosine_similarity

# Calculate similarity matrix
similarity_matrix = cosine_similarity(user_features)

# Find similar users
similar_users = similarity_matrix[user_id].argsort()[-k:][::-1]
```

#### c.3. Clustering

```python
from sklearn.cluster import KMeans

# User clustering
kmeans = KMeans(n_clusters=5, random_state=42)
user_clusters = kmeans.fit_predict(user_features)
```

### d. Hybrid Recommendation System

#### d.1. Weighted Hybrid

- Kết hợp nhiều thuật toán với trọng số
- Tối ưu hóa trọng số dựa trên performance
- Adaptive weighting based on user behavior

#### d.2. Cascade Hybrid

- Áp dụng thuật toán theo thứ tự
- Filter và rank kết quả
- Improve recommendation quality

#### d.3. Feature Combination

- Combine features từ nhiều nguồn
- Multi-modal recommendation
- Enhanced user modeling

### e. Performance Evaluation

#### e.1. Metrics

- **Precision@k**: Độ chính xác trong top-k recommendations
- **Recall@k**: Độ bao phủ trong top-k recommendations
- **NDCG**: Normalized Discounted Cumulative Gain
- **MAP**: Mean Average Precision

#### e.2. Cross-validation

- **Leave-one-out**: Đánh giá trên từng user
- **Time-based split**: Chia theo thời gian
- **Stratified sampling**: Đảm bảo balance

## 2.2.9. Docker Containerization

### a. Định nghĩa và Khái niệm

Docker là một nền tảng để phát triển, vận chuyển và chạy ứng dụng trong các container. Container là các gói nhỏ chứa tất cả những gì cần thiết để chạy ứng dụng, bao gồm code, runtime, system tools, libraries và settings.

### b. Kiến trúc Docker

#### b.1. Docker Engine

- **Docker Daemon**: Background service quản lý containers
- **Docker CLI**: Command-line interface
- **REST API**: API để tương tác với Docker

#### b.2. Container Architecture

- **Namespaces**: Isolation cho processes, network, filesystem
- **Control Groups**: Resource limiting và monitoring
- **Union File Systems**: Layered filesystem

### c. Docker Components

#### c.1. Images

- **Base Images**: Ubuntu, Python, Node.js
- **Application Images**: Custom images cho ứng dụng
- **Multi-stage Builds**: Optimize image size

#### c.2. Containers

- **Running Instances**: Active containers từ images
- **Container Lifecycle**: Create, start, stop, remove
- **Resource Management**: CPU, memory, disk limits

#### c.3. Docker Compose

```yaml
version: "3.8"
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: movie_mate
  redis:
    image: redis:6-alpine
```

### d. Benefits trong dự án

#### d.1. Environment Consistency

- Same environment across development, staging, production
- Eliminate "works on my machine" issues
- Easy setup cho new developers

#### d.2. Scalability

- Horizontal scaling với multiple containers
- Load balancing
- Microservices architecture

#### d.3. Deployment

- Easy deployment to cloud platforms
- Blue-green deployment
- Rollback capabilities

## 2.2.10. Nginx Web Server

### a. Định nghĩa và Vai trò

Nginx là một web server mã nguồn mở, có thể hoạt động như reverse proxy, load balancer, HTTP cache và mail proxy. Nginx được thiết kế để xử lý nhiều kết nối đồng thời với hiệu suất cao và sử dụng tài nguyên hiệu quả.

### b. Kiến trúc và Event-driven Model

#### b.1. Master-Worker Process Model

- **Master Process**: Quản lý worker processes
- **Worker Processes**: Xử lý client requests
- **Event-driven**: Non-blocking I/O operations

#### b.2. Connection Handling

- **Asynchronous**: Xử lý nhiều connections đồng thời
- **Non-blocking**: Không block khi waiting for I/O
- **Event-driven**: React to events efficiently

### c. Configuration và Features

#### c.1. Basic Configuration

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### c.2. Load Balancing

```nginx
upstream backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

#### c.3. Caching

- **Static File Caching**: Cache static assets
- **Proxy Caching**: Cache backend responses
- **Microcaching**: Short-term caching

### d. Security Features

#### d.1. SSL/TLS Termination

- **SSL Certificates**: Handle HTTPS connections
- **HTTP/2 Support**: Modern protocol support
- **Security Headers**: Add security headers

#### d.2. Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api/ {
    limit_req zone=api burst=20 nodelay;
}
```

#### d.3. Access Control

- **IP-based Access**: Allow/deny specific IPs
- **Authentication**: Basic auth, JWT validation
- **CORS**: Cross-origin resource sharing

## 2.2.11. Gunicorn WSGI Server

### a. Định nghĩa và Mục đích

Gunicorn (Green Unicorn) là một WSGI HTTP Server cho Python web applications. Gunicorn được thiết kế để chạy các ứng dụng Python web trong production environment với hiệu suất cao và ổn định.

### b. Kiến trúc và Worker Models

#### b.1. Master-Worker Architecture

- **Master Process**: Quản lý worker processes
- **Worker Processes**: Xử lý HTTP requests
- **Process Management**: Auto-restart failed workers

#### b.2. Worker Types

- **Sync Workers**: Traditional synchronous workers
- **Async Workers**: Eventlet, gevent, tornado
- **Thread Workers**: Multi-threaded workers

### c. Configuration và Optimization

#### c.1. Basic Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
```

#### c.2. Performance Tuning

- **Worker Count**: Optimal number of workers
- **Worker Class**: Choose appropriate worker type
- **Connection Handling**: Manage connections efficiently

#### c.3. Monitoring và Logging

- **Access Logs**: Log HTTP requests
- **Error Logs**: Log errors and exceptions
- **Metrics**: Performance metrics collection

### d. Integration với Nginx

#### d.1. Reverse Proxy Setup

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

#### d.2. Load Balancing

- **Multiple Gunicorn Instances**: Run multiple instances
- **Health Checks**: Monitor worker health
- **Graceful Reloading**: Reload without downtime

## 2.2.12. PayPal API Integration

### a. Định nghĩa và Tổng quan

PayPal API là bộ công cụ cho phép tích hợp thanh toán PayPal vào ứng dụng web. PayPal cung cấp nhiều loại API khác nhau để xử lý thanh toán, subscription, refund và các dịch vụ tài chính khác.

### b. PayPal API Types

#### b.1. REST APIs

- **Payments API**: Xử lý thanh toán trực tiếp
- **Orders API**: Tạo và quản lý orders
- **Subscriptions API**: Quản lý đăng ký định kỳ
- **Payouts API**: Chuyển tiền hàng loạt

#### b.2. Webhooks

- **Event Notifications**: Real-time notifications
- **Payment Status Updates**: Cập nhật trạng thái thanh toán
- **Subscription Events**: Events từ subscriptions

### c. Implementation trong dự án

#### c.1. Payment Processing

```python
import paypalrestsdk

paypalrestsdk.configure({
    "mode": "sandbox",  # sandbox or live
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
})

# Create payment
payment = paypalrestsdk.Payment({
    "intent": "sale",
    "payer": {
        "payment_method": "paypal"
    },
    "redirect_urls": {
        "return_url": "http://localhost:3000/success",
        "cancel_url": "http://localhost:3000/cancel"
    },
    "transactions": [{
        "item_list": {
            "items": [{
                "name": "Premium Subscription",
                "sku": "premium-monthly",
                "price": "9.99",
                "currency": "USD",
                "quantity": 1
            }]
        },
        "amount": {
            "total": "9.99",
            "currency": "USD"
        },
        "description": "Premium subscription for MovieMate"
    }]
})
```

#### c.2. Subscription Management

```python
# Create subscription
subscription = paypalrestsdk.BillingPlan({
    "name": "Premium Monthly",
    "description": "Premium subscription monthly plan",
    "type": "FIXED",
    "payment_definitions": [{
        "name": "Regular Payments",
        "type": "REGULAR",
        "frequency": "MONTH",
        "frequency_interval": "1",
        "amount": {
            "value": "9.99",
            "currency": "USD"
        },
        "cycles": "0"
    }],
    "merchant_preferences": {
        "setup_fee": {
            "value": "0",
            "currency": "USD"
        },
        "return_url": "http://localhost:3000/success",
        "cancel_url": "http://localhost:3000/cancel"
    }
})
```

### d. Security và Best Practices

#### d.1. Security Measures

- **HTTPS**: Sử dụng HTTPS cho tất cả communications
- **Webhook Verification**: Verify webhook signatures
- **Input Validation**: Validate tất cả input data
- **Error Handling**: Proper error handling và logging

#### d.2. Testing

- **Sandbox Environment**: Test trong sandbox trước
- **Webhook Testing**: Test webhook endpoints
- **Error Scenarios**: Test various error conditions

#### d.3. Production Considerations

- **Live Environment**: Switch to live environment
- **Monitoring**: Monitor payment processing
- **Backup Plans**: Have backup payment methods
- **Compliance**: Ensure PCI DSS compliance

### e. Integration Benefits

#### e.1. User Experience

- **Familiar Interface**: Users familiar with PayPal
- **Quick Checkout**: Fast and secure checkout
- **Mobile Support**: Excellent mobile experience

#### e.2. Business Benefits

- **Global Reach**: Accept payments worldwide
- **Multiple Currencies**: Support various currencies
- **Fraud Protection**: Built-in fraud protection
- **Analytics**: Payment analytics và reporting

---

_Phần cơ sở lý thuyết này cung cấp nền tảng kiến thức vững chắc cho việc hiểu và triển khai các công nghệ trong hệ thống Movie Recommendation System. Mỗi công nghệ được phân tích chi tiết về định nghĩa, kiến trúc, tính năng và ứng dụng cụ thể trong dự án._
