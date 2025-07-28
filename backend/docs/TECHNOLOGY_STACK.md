# MOVIE MATE V2 - TECHNOLOGY STACK

## 🎯 TỔNG QUAN KIẾN TRÚC

Movie Mate v2 là một hệ thống khuyến nghị phim full-stack sử dụng kiến trúc microservices với các công nghệ hiện đại.

---

## 🚀 BACKEND TECHNOLOGIES

### 🐍 Core Framework & Language

| Technology                | Version | Mô tả                    |
| ------------------------- | ------- | ------------------------ |
| **Python**                | 3.11+   | Ngôn ngữ lập trình chính |
| **Django**                | 4.0+    | Web framework chính      |
| **Django REST Framework** | 3.14.0+ | API framework            |

### 🔐 Authentication & Security

| Technology                          | Version | Mô tả                         |
| ----------------------------------- | ------- | ----------------------------- |
| **Django REST Framework SimpleJWT** | 5.3.0+  | JWT Authentication            |
| **Django CORS Headers**             | 4.3.0+  | Cross-Origin Resource Sharing |
| **Google OAuth2**                   | -       | Social authentication         |
| **WhiteNoise**                      | 6.6.0+  | Static files serving          |

### 🗄️ Database & Caching

| Technology          | Version    | Mô tả                    |
| ------------------- | ---------- | ------------------------ |
| **PostgreSQL**      | 15-alpine  | Primary database         |
| **Redis**           | 7.0-alpine | Caching & message broker |
| **Django Redis**    | 5.4.0+     | Django-Redis integration |
| **psycopg2-binary** | 2.9.9+     | PostgreSQL adapter       |

### 🔍 Search & Data Processing

| Technology                   | Version | Mô tả                            |
| ---------------------------- | ------- | -------------------------------- |
| **Elasticsearch**            | 7.17.9  | Full-text search engine          |
| **elasticsearch-dsl**        | 7.4.0   | Elasticsearch DSL for Python     |
| **django-elasticsearch-dsl** | 7.2.2   | Django-Elasticsearch integration |
| **BeautifulSoup4**           | 4.12.0+ | Web scraping                     |
| **lxml**                     | 4.9.0+  | XML/HTML processing              |

### ⚙️ Task Queue & Background Processing

| Technology                | Version | Mô tả                   |
| ------------------------- | ------- | ----------------------- |
| **Celery**                | 5.2.0+  | Distributed task queue  |
| **django-celery-beat**    | -       | Periodic task scheduler |
| **django-celery-results** | -       | Task result backend     |
| **Flower**                | -       | Celery monitoring tool  |

### 🤖 Machine Learning & Recommendation

| Technology          | Version | Mô tả                      |
| ------------------- | ------- | -------------------------- |
| **scikit-learn**    | 1.3.2   | General ML algorithms      |
| **scikit-surprise** | 1.1.4   | Collaborative filtering    |
| **TensorFlow**      | 2.15.0  | Deep learning framework    |
| **Keras**           | 2.15.0  | High-level neural networks |
| **pandas**          | 2.1.4   | Data manipulation          |
| **numpy**           | 1.25.2  | Numerical computations     |
| **scipy**           | 1.11.4  | Scientific computing       |

### 📊 Data Analysis & Visualization

| Technology     | Version | Mô tả                     |
| -------------- | ------- | ------------------------- |
| **matplotlib** | 3.8.2   | Plotting library          |
| **seaborn**    | 0.13.0  | Statistical visualization |
| **plotly**     | 5.17.0  | Interactive plots         |

### 🧠 Natural Language Processing

| Technology | Version | Mô tả                       |
| ---------- | ------- | --------------------------- |
| **NLTK**   | 3.8.1   | Natural language processing |
| **spaCy**  | 3.7.2   | Advanced NLP                |
| **gensim** | 4.3.2   | Topic modeling & embeddings |

### 🔧 Feature Engineering & Optimization

| Technology            | Version | Mô tả                       |
| --------------------- | ------- | --------------------------- |
| **category-encoders** | 2.6.3   | Categorical encoding        |
| **feature-engine**    | 1.6.2   | Feature engineering         |
| **optuna**            | 3.4.0   | Hyperparameter optimization |
| **mlflow**            | 2.8.1   | ML experiment tracking      |
| **hyperopt**          | 0.2.7   | Bayesian optimization       |

### ⚡ Performance & Optimization

| Technology   | Version   | Mô tả                        |
| ------------ | --------- | ---------------------------- |
| **joblib**   | 1.3.2     | Parallel processing          |
| **numba**    | 0.58.1    | JIT compiler                 |
| **dask**     | 2023.12.1 | Parallel computing           |
| **sparse**   | 0.14.0    | Sparse matrix operations     |
| **implicit** | 0.7.2     | Fast collaborative filtering |

### 📋 API Documentation & Utils

| Technology         | Version | Mô tả                         |
| ------------------ | ------- | ----------------------------- |
| **drf-yasg**       | 1.21.7+ | Swagger/OpenAPI documentation |
| **django-filter**  | 23.5+   | API filtering                 |
| **django-environ** | 0.11.2+ | Environment variables         |
| **python-dotenv**  | 1.0.0+  | Environment file loading      |
| **requests**       | 2.0.0+  | HTTP library                  |

### 🧪 Testing & Development

| Technology           | Version | Mô tả                  |
| -------------------- | ------- | ---------------------- |
| **pytest-benchmark** | 4.0.0   | Performance testing    |
| **memory-profiler**  | 0.61.0  | Memory usage profiling |
| **tqdm**             | 4.66.1  | Progress bars          |

### 🏭 Model Serving & Deployment

| Technology      | Version | Mô tả                 |
| --------------- | ------- | --------------------- |
| **ONNX**        | 1.15.0  | Model exchange format |
| **onnxruntime** | 1.16.3  | ONNX runtime          |
| **pyarrow**     | 14.0.1  | Columnar data format  |

---

## 🎨 FRONTEND TECHNOLOGIES

### ⚛️ Core Framework & Libraries

| Technology           | Version | Mô tả               |
| -------------------- | ------- | ------------------- |
| **React**            | 18.2.0  | Frontend framework  |
| **React DOM**        | 18.2.0  | React rendering     |
| **React Router DOM** | 6.30.0  | Client-side routing |
| **React Scripts**    | 5.0.1   | Build tools         |

### 🎭 UI Components & Styling

| Technology              | Version | Mô tả                   |
| ----------------------- | ------- | ----------------------- |
| **Material-UI (MUI)**   | 7.1.1   | React component library |
| **@mui/icons-material** | 7.1.1   | Material icons          |
| **@emotion/react**      | 11.14.0 | CSS-in-JS library       |
| **@emotion/styled**     | 11.14.0 | Styled components       |
| **TailwindCSS**         | -       | Utility-first CSS       |
| **TailwindCSS Animate** | 1.0.7   | Animation utilities     |
| **Headless UI**         | 2.2.4   | Unstyled components     |
| **Heroicons**           | 2.2.0   | Icon library            |
| **Lucide React**        | 0.508.0 | Icon components         |
| **React Icons**         | 5.5.0   | Popular icon libraries  |

### 📊 State Management & Data Fetching

| Technology                  | Version | Mô tả                   |
| --------------------------- | ------- | ----------------------- |
| **Redux Toolkit**           | 2.8.1   | State management        |
| **React Redux**             | 9.2.0   | React-Redux bindings    |
| **TanStack Query**          | 5.76.0  | Server state management |
| **TanStack Query DevTools** | 5.0.0   | Query debugging         |
| **Immer**                   | 10.1.1  | Immutable state updates |

### 🌐 HTTP & API Communication

| Technology | Version | Mô tả       |
| ---------- | ------- | ----------- |
| **Axios**  | 1.9.0   | HTTP client |

### 🎨 Animation & Interaction

| Technology                      | Version | Mô tả                     |
| ------------------------------- | ------- | ------------------------- |
| **Framer Motion**               | 12.9.4  | Animation library         |
| **React Scroll**                | 1.9.3   | Scroll utilities          |
| **React Intersection Observer** | 9.16.0  | Intersection Observer API |
| **Swiper**                      | 11.2.6  | Touch slider              |

### 📈 Charts & Visualization

| Technology           | Version | Mô tả                      |
| -------------------- | ------- | -------------------------- |
| **Chart.js**         | 4.5.0   | Chart library              |
| **React Chart.js 2** | 5.3.0   | React wrapper for Chart.js |

### 🔐 Authentication & Payments

| Technology             | Version | Mô tả                 |
| ---------------------- | ------- | --------------------- |
| **Google OAuth React** | 0.12.2  | Google authentication |
| **PayPal React**       | 8.8.3   | PayPal integration    |

### 🌍 Internationalization

| Technology                           | Version | Mô tả                |
| ------------------------------------ | ------- | -------------------- |
| **i18next**                          | 23.16.8 | Internationalization |
| **react-i18next**                    | 14.1.3  | React i18n bindings  |
| **i18next-browser-languagedetector** | 7.2.0   | Language detection   |
| **i18next-http-backend**             | 2.4.2   | Backend loading      |

### 🔧 Utilities & Tools

| Technology          | Version | Mô tả                     |
| ------------------- | ------- | ------------------------- |
| **date-fns**        | 4.1.0   | Date utility library      |
| **React Hot Toast** | 2.5.2   | Toast notifications       |
| **React Toastify**  | 11.0.5  | Alternative toast library |
| **React Window**    | 1.8.11  | Virtualization            |
| **dotenv**          | 16.5.0  | Environment variables     |

### 🧪 Testing

| Technology                      | Version | Mô tả                    |
| ------------------------------- | ------- | ------------------------ |
| **Testing Library**             | -       | Testing utilities        |
| **@testing-library/react**      | 16.3.0  | React testing            |
| **@testing-library/jest-dom**   | 6.6.3   | Jest DOM matchers        |
| **@testing-library/user-event** | 13.5.0  | User interaction testing |

### 🛠️ Development Tools

| Technology                  | Version | Mô tả                    |
| --------------------------- | ------- | ------------------------ |
| **ESLint**                  | 8.57.1  | Code linting             |
| **Prettier**                | 3.5.3   | Code formatting          |
| **webpack-bundle-analyzer** | 4.9.1   | Bundle analysis          |
| **Puppeteer**               | 24.10.2 | Headless browser testing |

---

## 🐳 CONTAINERIZATION & DEPLOYMENT

### 🐋 Docker

| Technology            | Version    | Mô tả                         |
| --------------------- | ---------- | ----------------------------- |
| **Docker**            | -          | Containerization platform     |
| **Docker Compose**    | 3.8        | Multi-container orchestration |
| **Python Base Image** | 3.11-slim  | Lightweight Python runtime    |
| **PostgreSQL Image**  | 15-alpine  | Database container            |
| **Redis Image**       | 7.0-alpine | Cache container               |

### 🚀 Services Architecture

```yaml
Services trong Docker Compose:
├── web (Django Backend)
├── postgres (Database)
├── redis (Cache & Message Broker)
├── celery_worker (Background Tasks)
├── celery_beat (Scheduled Tasks)
└── flower (Task Monitoring)
```

---

## 🛠️ DEVELOPMENT & DEPLOYMENT TOOLS

### 📝 Configuration Management

| Technology             | Purpose                        |
| ---------------------- | ------------------------------ |
| **Environment Files**  | `.env`, `.env.local`           |
| **Django Settings**    | Modular settings configuration |
| **Docker Environment** | Container configuration        |

### 📊 Monitoring & Logging

| Technology           | Purpose               |
| -------------------- | --------------------- |
| **Django Logging**   | Application logging   |
| **Celery Flower**    | Task queue monitoring |
| **Redis Monitoring** | Cache monitoring      |

### 🔒 Security Features

| Technology             | Purpose                               |
| ---------------------- | ------------------------------------- |
| **JWT Authentication** | Stateless authentication              |
| **CORS Configuration** | Cross-origin security                 |
| **CSRF Protection**    | Cross-site request forgery protection |
| **HTTPS Enforcement**  | Secure communication                  |
| **Rate Limiting**      | API abuse prevention                  |

---

## 📦 DEPLOYMENT PLATFORMS

### ☁️ Cloud Platforms

| Platform   | Usage                  |
| ---------- | ---------------------- |
| **Vercel** | Frontend deployment    |
| **Render** | Backend deployment     |
| **GitHub** | Source code management |

---

## 🧮 PERFORMANCE OPTIMIZATION

### ⚡ Backend Optimization

- **Redis Caching**: Query result caching
- **Database Indexing**: Optimized queries
- **Celery Tasks**: Asynchronous processing
- **Connection Pooling**: Database connections
- **Static File Serving**: WhiteNoise compression

### 🎯 Frontend Optimization

- **Code Splitting**: Dynamic imports
- **Bundle Analysis**: Webpack analyzer
- **Image Optimization**: Lazy loading
- **Virtual Scrolling**: React Window
- **Performance Monitoring**: Lighthouse integration

---

## 📈 ANALYTICS & MONITORING

### 📊 Performance Metrics

- **Lighthouse**: Web performance auditing
- **Bundle Analysis**: JavaScript optimization
- **Memory Profiling**: Python memory usage
- **Query Performance**: Database optimization

---

## 🎯 MACHINE LEARNING PIPELINE

### 🤖 Recommendation Algorithms

- **Collaborative Filtering**: User-based & Item-based
- **Demographic Filtering**: Enhanced 29-dimensional vectors
- **Content-based Filtering**: Movie features
- **Hybrid Approach**: Combined algorithms

### 📊 Data Processing Pipeline

- **ETL Processing**: Data extraction & transformation
- **Feature Engineering**: Advanced vectorization
- **Model Training**: Automated pipelines
- **Model Evaluation**: Comprehensive metrics

---

## 🏗️ ARCHITECTURE SUMMARY

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   React.js      │◄──►│    Django       │◄──►│  PostgreSQL     │
│   Redux         │    │    DRF          │    │                 │
│   Material-UI   │    │    Celery       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Cache       │    │     Search      │
                       │     Redis       │    │ Elasticsearch   │
                       └─────────────────┘    └─────────────────┘
```

**🎉 TOTAL: 80+ Technologies và Tools được sử dụng trong Movie Mate v2!**
