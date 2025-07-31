# PHỤ LỤC: LÝ THUYẾT NÂNG CAO

## A.1. CONTENT-BASED FILTERING

### A.1.1. Nguyên lý hoạt động

Content-Based Filtering là phương pháp khuyến nghị dựa trên đặc tính nội dung của sản phẩm và lịch sử tương tác của người dùng. Phương pháp này hoạt động theo nguyên tắc "nếu người dùng thích một sản phẩm, họ cũng sẽ thích những sản phẩm tương tự".

### A.1.2. Đặc trưng của phim

**Các đặc trưng chính:**

- **Thể loại (Genre)**: Hành động, Tình cảm, Kinh dị, Hài hước...
- **Diễn viên (Cast)**: Tên diễn viên chính, phụ
- **Đạo diễn (Director)**: Người đạo diễn
- **Năm sản xuất (Year)**: Thời gian phát hành
- **Ngôn ngữ (Language)**: Tiếng Việt, Anh, Hàn...
- **Độ dài (Duration)**: Thời lượng phim
- **Đánh giá (Rating)**: Điểm đánh giá từ cộng đồng
- **Mô tả (Overview)**: Nội dung tóm tắt

### A.1.3. Vector hóa nội dung

**TF-IDF (Term Frequency-Inverse Document Frequency):**

```
TF-IDF(t,d) = TF(t,d) × IDF(t)
```

Trong đó:

- `TF(t,d)`: Tần suất xuất hiện của từ t trong tài liệu d
- `IDF(t)`: log(N/df(t)) với N là tổng số tài liệu, df(t) là số tài liệu chứa từ t

### A.1.4. Tính toán độ tương đồng

**Cosine Similarity:**

```
sim(movie1, movie2) = (movie1_vector · movie2_vector) / (||movie1_vector|| × ||movie2_vector||)
```

### A.1.5. Ưu điểm và nhược điểm

**Ưu điểm:**

- Không cần dữ liệu từ nhiều người dùng
- Có thể đề xuất cho người dùng mới
- Giải thích được lý do đề xuất
- Không bị ảnh hưởng bởi Cold Start

**Nhược điểm:**

- Cần phân tích nội dung chi tiết
- Khó phát hiện sở thích ẩn
- Phụ thuộc vào chất lượng metadata
- Có thể tạo ra "filter bubble"

## A.2. MATRIX FACTORIZATION

### A.2.1. Nguyên lý cơ bản

Matrix Factorization là kỹ thuật phân rã ma trận đánh giá thành tích của hai ma trận có chiều thấp hơn:

```
R ≈ P × Q^T
```

Trong đó:

- `R`: Ma trận đánh giá (users × items)
- `P`: Ma trận đặc trưng người dùng (users × k)
- `Q`: Ma trận đặc trưng sản phẩm (items × k)
- `k`: Số chiều ẩn (latent factors)

### A.2.2. Thuật toán SVD (Singular Value Decomposition)

**Công thức:**

```
R = U × Σ × V^T
```

Trong đó:

- `U`: Ma trận eigenvectors của R × R^T
- `Σ`: Ma trận diagonal chứa singular values
- `V`: Ma trận eigenvectors của R^T × R

### A.2.3. Thuật toán ALS (Alternating Least Squares)

**Mục tiêu:**

```
minimize ||R - P × Q^T||² + λ(||P||² + ||Q||²)
```

**Cập nhật:**

```
P = (Q^T × Q + λI)^(-1) × Q^T × R
Q = (P^T × P + λI)^(-1) × P^T × R^T
```

## A.3. DEEP LEARNING TRONG RECOMMENDATION

### A.3.1. Neural Collaborative Filtering (NCF)

**Kiến trúc:**

1. **Input Layer**: User ID và Item ID
2. **Embedding Layer**: Chuyển đổi ID thành vector
3. **Hidden Layers**: MLP layers
4. **Output Layer**: Dự đoán rating

**Công thức:**

```
y = σ(W^T × φ(W^T × φ(...φ(W^T × [p_u, q_i]))))
```

### A.3.2. Wide & Deep Learning

**Wide Component:**

- Linear model với feature engineering
- Xử lý các tương tác đơn giản

**Deep Component:**

- Neural network với embedding
- Học các tương tác phức tạp

**Kết hợp:**

```
P(y|x) = σ(W_wide^T × [x, φ(x)] + W_deep^T × a^(l_f) + b)
```

## A.4. EVALUATION METRICS CHI TIẾT

### A.4.1. Ranking Metrics

**Precision@K:**

```
Precision@K = (Number of relevant items in top K) / K
```

**Recall@K:**

```
Recall@K = (Number of relevant items in top K) / (Total relevant items)
```

**NDCG@K (Normalized Discounted Cumulative Gain):**

```
NDCG@K = DCG@K / IDCG@K
```

Trong đó:

```
DCG@K = Σ(i=1 to K) (2^relevance_i - 1) / log2(i + 1)
```

### A.4.2. Diversity Metrics

**Intra-List Similarity:**

```
ILS = (2 / (N × (N-1))) × Σ(i=1 to N-1) Σ(j=i+1 to N) sim(item_i, item_j)
```

**Coverage:**

```
Coverage = |∪(recommended items for all users)| / |total items|
```

### A.4.3. Novelty Metrics

**Average Popularity:**

```
AP = (1 / N) × Σ(i=1 to N) log2(popularity(item_i))
```

**Long-tail Coverage:**

```
LTC = |long_tail_items_in_recommendations| / |total_long_tail_items|
```

## A.5. OPTIMIZATION TECHNIQUES

### A.5.1. Hyperparameter Tuning

**Grid Search:**

- Tìm kiếm có hệ thống trong không gian tham số
- Tốn thời gian nhưng đảm bảo tìm được tối ưu

**Random Search:**

- Lấy mẫu ngẫu nhiên từ không gian tham số
- Hiệu quả hơn Grid Search trong nhiều trường hợp

**Bayesian Optimization:**

- Sử dụng Gaussian Process để dự đoán hiệu năng
- Tối ưu hóa thông minh với ít thử nghiệm

### A.5.2. Regularization Techniques

**L1 Regularization (Lasso):**

```
Loss = Original_Loss + λ × Σ|w_i|
```

**L2 Regularization (Ridge):**

```
Loss = Original_Loss + λ × Σ(w_i)²
```

**Dropout:**

- Ngẫu nhiên loại bỏ một số neurons trong training
- Giảm overfitting

### A.5.3. Learning Rate Scheduling

**Step Decay:**

```
lr = lr_0 × γ^(epoch // step_size)
```

**Exponential Decay:**

```
lr = lr_0 × γ^epoch
```

**Cosine Annealing:**

```
lr = lr_min + (lr_max - lr_min) × (1 + cos(epoch × π / T)) / 2
```

## A.6. SCALABILITY AND PERFORMANCE

### A.6.1. Distributed Computing

**MapReduce Framework:**

- Chia nhỏ bài toán thành các task độc lập
- Xử lý song song trên nhiều máy

**Spark MLlib:**

- In-memory computing
- Hỗ trợ nhiều thuật toán ML

### A.6.2. Caching Strategies

**Redis Cache:**

- Lưu trữ kết quả tính toán
- Giảm thời gian phản hồi

**CDN (Content Delivery Network):**

- Phân tán nội dung tĩnh
- Tăng tốc độ truy cập

### A.6.3. Database Optimization

**Indexing:**

- B-tree index cho user_id, item_id
- Composite index cho (user_id, item_id)

**Partitioning:**

- Chia dữ liệu theo user_id hoặc timestamp
- Giảm thời gian truy vấn

## A.7. ETHICAL CONSIDERATIONS

### A.7.1. Privacy Protection

**Differential Privacy:**

- Thêm noise vào dữ liệu
- Bảo vệ thông tin cá nhân

**Federated Learning:**

- Học trên thiết bị người dùng
- Không chia sẻ dữ liệu raw

### A.7.2. Bias and Fairness

**Algorithmic Bias:**

- Kiểm tra bias trong dữ liệu training
- Cân bằng representation của các nhóm

**Fairness Metrics:**

- Demographic Parity
- Equalized Odds
- Individual Fairness

### A.7.3. Transparency

**Explainable AI:**

- Giải thích lý do đề xuất
- Tăng độ tin cậy của hệ thống

**Audit Trail:**

- Ghi lại quá trình ra quyết định
- Dễ dàng debug và cải thiện

## A.8. FUTURE TRENDS

### A.8.1. Multi-Modal Recommendation

**Text + Image + Audio:**

- Kết hợp nhiều loại dữ liệu
- Tăng độ chính xác dự đoán

**Cross-Modal Learning:**

- Học mapping giữa các modality
- Transfer learning

### A.8.2. Context-Aware Recommendation

**Temporal Context:**

- Thời gian trong ngày, mùa
- Xu hướng theo thời gian

**Location Context:**

- Vị trí địa lý
- Văn hóa địa phương

**Social Context:**

- Mạng xã hội
- Ảnh hưởng từ bạn bè

### A.8.3. Reinforcement Learning

**Multi-Armed Bandit:**

- Cân bằng exploration vs exploitation
- Học online

**Deep Reinforcement Learning:**

- DQN, A3C, PPO
- Tối ưu hóa long-term reward

## A.9. IMPLEMENTATION BEST PRACTICES

### A.9.1. Code Architecture

**Modular Design:**

- Tách biệt các component
- Dễ maintain và test

**Configuration Management:**

- External configuration files
- Environment-specific settings

**Logging and Monitoring:**

- Structured logging
- Performance metrics

### A.9.2. Testing Strategies

**Unit Testing:**

- Test từng function riêng lẻ
- Mock external dependencies

**Integration Testing:**

- Test interaction giữa components
- End-to-end testing

**A/B Testing:**

- So sánh hiệu năng các thuật toán
- Statistical significance

### A.9.3. Deployment

**CI/CD Pipeline:**

- Automated testing
- Continuous deployment

**Containerization:**

- Docker containers
- Kubernetes orchestration

**Monitoring:**

- Health checks
- Alert systems
