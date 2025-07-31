# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT

## 2.1. TỔNG QUAN VỀ HỆ THỐNG KHUYẾN NGHỊ

### 2.1.1. Định nghĩa và khái niệm

Hệ thống khuyến nghị (Recommendation System) là một hệ thống thông minh được thiết kế để tự động đề xuất các sản phẩm, dịch vụ hoặc nội dung phù hợp với sở thích và nhu cầu của người dùng. Đây là một nhánh quan trọng của trí tuệ nhân tạo (Artificial Intelligence) và khai thác dữ liệu (Data Mining), được ứng dụng rộng rãi trong nhiều lĩnh vực như thương mại điện tử, giải trí, giáo dục và truyền thông.

Trong bối cảnh nền tảng xem phim trực tuyến, hệ thống khuyến nghị đóng vai trò quan trọng trong việc:

- **Cá nhân hóa trải nghiệm người dùng**: Đề xuất phim phù hợp với sở thích cá nhân, thói quen xem phim và đặc điểm nhân khẩu học
- **Tăng cường tương tác và thời gian sử dụng**: Khuyến khích người dùng khám phá nội dung mới, tăng tỷ lệ xem phim
- **Giải quyết vấn đề thông tin quá tải**: Lọc và sắp xếp nội dung từ kho dữ liệu khổng lồ theo mức độ phù hợp
- **Tối ưu hóa doanh thu và hiệu quả kinh doanh**: Tăng tỷ lệ chuyển đổi, giữ chân người dùng

### 2.1.2. Phân loại hệ thống khuyến nghị

Hệ thống khuyến nghị được phân thành ba nhóm chính dựa trên phương pháp tiếp cận:

#### a) Content-Based Filtering (Lọc dựa trên nội dung)

- **Nguyên lý**: Dựa trên đặc tính và thuộc tính của sản phẩm
- **Dữ liệu đầu vào**: Thông tin mô tả sản phẩm (thể loại, diễn viên, đạo diễn, từ khóa...)
- **Ưu điểm**: Không cần dữ liệu từ người dùng khác, giải thích được lý do đề xuất
- **Nhược điểm**: Cần phân tích nội dung chi tiết, khó phát hiện sở thích ẩn

#### b) Collaborative Filtering (Lọc cộng tác)

- **Nguyên lý**: Dựa trên hành vi và đánh giá của cộng đồng người dùng
- **Dữ liệu đầu vào**: Ma trận đánh giá người dùng - sản phẩm
- **Ưu điểm**: Phát hiện được sở thích ẩn, không cần phân tích nội dung
- **Nhược điểm**: Gặp vấn đề Cold Start, Sparsity

#### c) Hybrid Approaches (Phương pháp lai)

- **Nguyên lý**: Kết hợp nhiều phương pháp để tối ưu hóa kết quả
- **Dữ liệu đầu vào**: Đa dạng từ nhiều nguồn khác nhau
- **Ưu điểm**: Tận dụng ưu điểm của nhiều phương pháp, giảm thiểu nhược điểm
- **Nhược điểm**: Phức tạp trong triển khai và tối ưu hóa

### 2.1.3. Các thách thức trong hệ thống khuyến nghị

#### a) Cold Start Problem

- **Vấn đề**: Không thể đề xuất cho người dùng mới hoặc sản phẩm mới
- **Nguyên nhân**: Thiếu dữ liệu lịch sử để tính toán độ tương đồng
- **Giải pháp**: Sử dụng Demographic Filtering, Content-Based Filtering

#### b) Data Sparsity Problem

- **Vấn đề**: Ma trận đánh giá thường rất thưa thớt
- **Nguyên nhân**: Người dùng chỉ đánh giá một phần nhỏ sản phẩm
- **Giải pháp**: Matrix Factorization, Dimensionality Reduction

#### c) Scalability Problem

- **Vấn đề**: Hiệu suất giảm khi số lượng người dùng/sản phẩm tăng
- **Nguyên nhân**: Độ phức tạp tính toán cao
- **Giải pháp**: Distributed Computing, Caching, Sampling

## 2.2. COLLABORATIVE FILTERING (CF)

### 2.2.1. Nguyên lý hoạt động

Collaborative Filtering là phương pháp khuyến nghị dựa trên nguyên tắc "những người dùng có sở thích tương tự sẽ thích những sản phẩm tương tự". Phương pháp này không cần phân tích nội dung của sản phẩm mà chỉ dựa vào:

- **Lịch sử đánh giá** của người dùng trong hệ thống
- **Mức độ tương đồng** giữa các người dùng hoặc sản phẩm
- **Patterns** và xu hướng trong hành vi đánh giá

### 2.2.2. Phân loại Collaborative Filtering

#### a) User-Based Collaborative Filtering

**Nguyên lý**: Tìm những người dùng có sở thích tương tự với người dùng mục tiêu, sau đó đề xuất các sản phẩm mà họ đã đánh giá cao.

**Quy trình thực hiện**:

1. Tính toán độ tương đồng giữa người dùng mục tiêu và tất cả người dùng khác
2. Chọn K người dùng có độ tương đồng cao nhất (K-nearest neighbors)
3. Dự đoán đánh giá dựa trên đánh giá trung bình của K người dùng này
4. Đề xuất sản phẩm có điểm dự đoán cao nhất

#### b) Item-Based Collaborative Filtering

**Nguyên lý**: Tìm những sản phẩm tương tự với các sản phẩm mà người dùng đã đánh giá cao, sau đó đề xuất những sản phẩm tương tự này.

**Quy trình thực hiện**:

1. Tính toán độ tương đồng giữa các cặp sản phẩm
2. Với mỗi sản phẩm chưa đánh giá, tính điểm dự đoán dựa trên đánh giá của người dùng cho các sản phẩm tương tự
3. Đề xuất các sản phẩm có điểm dự đoán cao nhất

### 2.2.3. Các phương pháp tính độ tương đồng

#### a) Cosine Similarity

Đo góc giữa hai vector đánh giá của người dùng:

```
sim(u,v) = (∑(r_ui × r_vi)) / (√(∑r_ui²) × √(∑r_vi²))
```

Trong đó:

- `r_ui`: Đánh giá của user u cho item i
- `r_vi`: Đánh giá của user v cho item i
- Kết quả nằm trong khoảng [-1, 1], càng gần 1 càng tương tự

#### b) Pearson Correlation

Đo mức độ tương quan tuyến tính giữa hai người dùng:

```
sim(u,v) = (∑(r_ui - r̄_u)(r_vi - r̄_v)) / (√(∑(r_ui - r̄_u)²) × √(∑(r_vi - r̄_v)²))
```

Trong đó:

- `r̄_u`: Đánh giá trung bình của user u
- `r̄_v`: Đánh giá trung bình của user v
- Phương pháp này hiệu quả hơn khi người dùng có xu hướng đánh giá khác nhau

#### c) Jaccard Similarity

Sử dụng cho dữ liệu nhị phân (like/dislike, xem/không xem):

```
sim(u,v) = |I_u ∩ I_v| / |I_u ∪ I_v|
```

Trong đó:

- `I_u`: Tập hợp items mà user u đã tương tác
- `I_v`: Tập hợp items mà user v đã tương tác

### 2.2.4. Công thức dự đoán đánh giá

#### a) Dự đoán đơn giản

```
pred(u,i) = r̄_u + (∑(sim(u,v) × (r_vi - r̄_v))) / (∑|sim(u,v)|)
```

#### b) Dự đoán có trọng số

```
pred(u,i) = (∑(sim(u,v) × r_vi)) / (∑|sim(u,v)|)
```

### 2.2.5. Ví dụ minh họa chi tiết

**Kịch bản**: Hệ thống có 4 người dùng (A, B, C, D) và 3 bộ phim (Fight Club, Doraemon, Inception)

| User | Fight Club | Doraemon | Inception |
| ---- | ---------- | -------- | --------- |
| A    | 5          | ?        | 4         |
| B    | 5          | 5        | 3         |
| C    | 2          | 1        | 5         |
| D    | 4          | 4        | 4         |

**Bước 1: Tính độ tương đồng giữa User A và các user khác**

Sử dụng Cosine Similarity:

- sim(A,B) = (5×5 + 4×3) / √(5²+4²) × √(5²+3²) = 37 / (6.4 × 5.8) = 0.99
- sim(A,C) = (5×2 + 4×5) / √(5²+4²) × √(2²+5²) = 30 / (6.4 × 5.4) = 0.87
- sim(A,D) = (5×4 + 4×4) / √(5²+4²) × √(4²+4²) = 36 / (6.4 × 5.7) = 0.99

**Bước 2: Chọn K-nearest neighbors**
Với K=2, chọn User B và User D (có độ tương đồng cao nhất)

**Bước 3: Dự đoán đánh giá cho Doraemon**

- User B đánh giá Doraemon: 5 điểm
- User D đánh giá Doraemon: 4 điểm
- Dự đoán: pred(A,Doraemon) = (0.99×5 + 0.99×4) / (0.99+0.99) = 4.5 điểm

**Kết quả**: Hệ thống đề xuất Doraemon cho User A với điểm dự đoán 4.5

### 2.2.6. Ưu điểm và nhược điểm

**Ưu điểm:**

- Không cần phân tích nội dung sản phẩm
- Có thể phát hiện sở thích ẩn mà người dùng không nhận ra
- Hiệu quả với dữ liệu đánh giá phong phú
- Dễ hiểu và triển khai
- Có thể áp dụng cho nhiều loại sản phẩm khác nhau

**Nhược điểm:**

- **Cold Start Problem**: Không thể đề xuất cho người dùng mới hoặc sản phẩm mới
- **Sparsity Problem**: Ma trận đánh giá thường thưa thớt, ảnh hưởng đến độ chính xác
- **Scalability**: Tính toán phức tạp khi số lượng người dùng lớn
- **Privacy Concerns**: Cần chia sẻ dữ liệu đánh giá cá nhân
- **Over-specialization**: Có thể tạo ra "bong bóng lọc", giới hạn sự đa dạng

## 2.3. DEMOGRAPHIC FILTERING

### 2.3.1. Nguyên lý hoạt động

Demographic Filtering là phương pháp khuyến nghị dựa trên đặc điểm nhân khẩu học của người dùng. Phương pháp này giải quyết vấn đề Cold Start bằng cách:

- **Phân tích thông tin cá nhân**: Tuổi, giới tính, nghề nghiệp, địa điểm, thu nhập, trình độ học vấn
- **Nhóm người dùng tương tự**: Dựa trên đặc điểm nhân khẩu học chung
- **Đề xuất dựa trên nhóm**: Sử dụng hành vi và sở thích của nhóm để dự đoán

### 2.3.2. Kỹ thuật phân cụm nhân khẩu học

#### a) Vector hóa thông tin người dùng

Hệ thống chuyển đổi thông tin nhân khẩu học thành vector số để có thể xử lý bằng các thuật toán machine learning:

```
User Vector = [Age_Bins, Gender, Occupation, Location, User_Type, Behavioral_Features]
```

**Chi tiết các thành phần:**

**1. Age Bins (6 features)**: Phân nhóm tuổi thành 6 khoảng

```
18-25: [1,0,0,0,0,0]
26-35: [0,1,0,0,0,0]
36-45: [0,0,1,0,0,0]
46-55: [0,0,0,1,0,0]
56-65: [0,0,0,0,1,0]
65+: [0,0,0,0,0,1]
```

**2. Gender (3 features)**: Mã hóa giới tính

```
Male: [1,0,0]
Female: [0,1,0]
Other: [0,0,1]
```

**3. Occupation (8 features)**: Phân loại nghề nghiệp

```
Student: [1,0,0,0,0,0,0,0]
Business: [0,1,0,0,0,0,0,0]
Technical: [0,0,1,0,0,0,0,0]
Creative: [0,0,0,1,0,0,0,0]
Service: [0,0,0,0,1,0,0,0]
Healthcare: [0,0,0,0,0,1,0,0]
Education: [0,0,0,0,0,0,1,0]
Other: [0,0,0,0,0,0,0,1]
```

**4. Location (4 features)**: Phân vùng địa lý

```
Urban: [1,0,0,0]
Suburban: [0,1,0,0]
Rural: [0,0,1,0]
International: [0,0,0,1]
```

**5. User Type (4 features)**: Loại tài khoản

```
Member: [1,0,0,0]
Premium Basic: [0,1,0,0]
Premium Pro: [0,0,1,0]
Admin: [0,0,0,1]
```

**6. Behavioral Features (4 features)**: Đặc điểm hành vi

```
Average Rating: [0.0 - 5.0]
Rating Variance: [0.0 - 2.0]
Rating Count: [0 - 1000]
Activity Level: [0.0 - 1.0]
```

#### b) K-Means Clustering

**Nguyên lý:**

- Nhóm người dùng có vector tương tự vào cùng cluster
- Mỗi cluster đại diện cho một nhóm nhân khẩu học cụ thể
- Sử dụng thuật toán K-Means để tối ưu hóa phân cụm

**Công thức tính khoảng cách Euclidean:**

```
distance(u,c) = √(∑(u_i - c_i)²)
```

**Quá trình phân cụm:**

1. Khởi tạo K centroids ngẫu nhiên trong không gian vector
2. Gán mỗi user vào centroid gần nhất dựa trên khoảng cách Euclidean
3. Cập nhật centroids bằng cách tính trung bình của tất cả users trong cluster
4. Lặp lại bước 2-3 cho đến khi centroids không thay đổi hoặc đạt số lần lặp tối đa

**Công thức cập nhật centroid:**

```
c_k = (1/|C_k|) × ∑(x_i ∈ C_k) x_i
```

Trong đó:

- `c_k`: Centroid của cluster k
- `C_k`: Tập hợp users trong cluster k
- `x_i`: Vector của user i

#### c) Rule-Based Clustering (Fallback)

Khi K-Means không khả dụng (thiếu dữ liệu, lỗi thuật toán), hệ thống sử dụng quy tắc đơn giản:

```
IF age BETWEEN 18-25 AND gender = 'M' THEN cluster = 'Young_Male'
IF age BETWEEN 18-25 AND gender = 'F' THEN cluster = 'Young_Female'
IF age BETWEEN 26-35 AND occupation = 'student' THEN cluster = 'Young_Professional'
IF age BETWEEN 26-35 AND occupation = 'business' THEN cluster = 'Business_Professional'
IF age BETWEEN 36-50 AND gender = 'M' THEN cluster = 'Middle_Aged_Male'
IF age BETWEEN 36-50 AND gender = 'F' THEN cluster = 'Middle_Aged_Female'
IF age > 50 THEN cluster = 'Senior'
```

### 2.3.3. Thuật toán đề xuất

#### a) Tìm người dùng tương tự

```
similar_users = find_users_in_same_cluster(target_user)
```

**Quy trình:**

1. Tạo vector nhân khẩu học cho người dùng mục tiêu
2. Tìm cluster phù hợp nhất dựa trên khoảng cách đến centroids
3. Lấy tất cả người dùng trong cluster đó
4. Tính độ tương đồng chi tiết với từng người dùng trong cluster

#### b) Tính điểm đề xuất

```
recommendation_score = average_rating(similar_users, movie) × similarity_weight
```

**Công thức chi tiết:**

```
score(movie) = (∑(rating_i × weight_i)) / (∑weight_i)
```

Trong đó:

- `rating_i`: Đánh giá của user i cho movie
- `weight_i`: Trọng số dựa trên độ tương đồng với target user

#### c) Xử lý Cold Start

**Cho người dùng mới (không có đánh giá):**

1. Tạo vector nhân khẩu học từ thông tin đăng ký
2. Tìm cluster phù hợp nhất dựa trên vector
3. Lấy top N phim được đánh giá cao nhất trong cluster
4. Đề xuất các phim này cho người dùng mới

**Cho người dùng có đánh giá:**

1. Kết hợp thông tin nhân khẩu học và lịch sử đánh giá
2. Tìm người dùng tương tự trong cluster có sở thích phim tương tự
3. Tính điểm dự đoán dựa trên đánh giá của những người dùng này
4. Đề xuất phim có điểm cao nhất

### 2.3.4. Ví dụ minh họa chi tiết

**Kịch bản**: User A (25 tuổi, Nam, Sinh viên, Hà Nội, Member) mới đăng ký

**Bước 1: Vector hóa thông tin**

```
User_A_Vector = [
    # Age Bins (6 features)
    1,0,0,0,0,0,  # 25 tuổi thuộc nhóm 18-25

    # Gender (3 features)
    1,0,0,  # Nam

    # Occupation (8 features)
    1,0,0,0,0,0,0,0,  # Student

    # Location (4 features)
    1,0,0,0,  # Urban (Hà Nội)

    # User Type (4 features)
    1,0,0,0,  # Member

    # Behavioral Features (4 features)
    0.0, 0.0, 0.0, 0.0  # Chưa có dữ liệu hành vi
]
```

**Bước 2: Phân cụm**

- Tính khoảng cách đến tất cả centroids
- Gán vào cluster có khoảng cách nhỏ nhất (ví dụ: Cluster_1)
- Cluster_1 chứa 150 người dùng tương tự (sinh viên nam 18-25 tuổi)

**Bước 3: Đề xuất**

- Lấy top 10 phim được đánh giá cao nhất trong Cluster_1
- Sắp xếp theo điểm trung bình và số lượng đánh giá
- Đề xuất cho User A

**Kết quả**: User A nhận được danh sách phim phù hợp với nhóm nhân khẩu học

### 2.3.5. Ưu điểm và nhược điểm

**Ưu điểm:**

- **Giải quyết Cold Start**: Có thể đề xuất cho người dùng mới ngay lập tức
- **Không cần lịch sử đánh giá**: Dựa trên thông tin cá nhân có sẵn
- **Dễ hiểu và giải thích**: Logic rõ ràng, minh bạch
- **Bảo mật**: Không chia sẻ dữ liệu đánh giá cá nhân
- **Tốc độ nhanh**: Không cần tính toán phức tạp
- **Ổn định**: Kết quả không thay đổi nhiều theo thời gian

**Nhược điểm:**

- **Độ chính xác thấp**: So với Collaborative Filtering khi có đủ dữ liệu
- **Stereotyping**: Có thể tạo ra định kiến và giả định không chính xác
- **Thiếu tính cá nhân hóa**: Chỉ dựa trên nhóm, không phản ánh sở thích cá nhân
- **Phụ thuộc vào dữ liệu nhân khẩu học**: Cần thông tin đầy đủ và chính xác
- **Không thích ứng**: Không học từ hành vi thay đổi của người dùng
- **Hạn chế đa dạng**: Có thể tạo ra "echo chamber" cho nhóm nhân khẩu học

## 2.4. HYBRID RECOMMENDATION SYSTEM

### 2.4.1. Nguyên lý kết hợp

Hệ thống Hybrid kết hợp nhiều phương pháp để tối ưu hóa kết quả và khắc phục nhược điểm của từng phương pháp riêng lẻ:

```
Final_Score = α × CF_Score + β × DF_Score + γ × CB_Score
```

Trong đó:

- `α, β, γ`: Trọng số của từng phương pháp (α + β + γ = 1)
- `CF_Score`: Điểm từ Collaborative Filtering
- `DF_Score`: Điểm từ Demographic Filtering
- `CB_Score`: Điểm từ Content-Based Filtering

### 2.4.2. Chiến lược kết hợp

#### a) Weighted Hybrid

Kết hợp điểm số từ nhiều phương pháp theo trọng số cố định:

```
recommendation_score = 0.4 × cf_score + 0.4 × df_score + 0.2 × cb_score
```

**Ưu điểm**: Đơn giản, dễ triển khai
**Nhược điểm**: Không thích ứng với từng người dùng

#### b) Switching Hybrid

Tự động chuyển đổi phương pháp tùy theo đặc điểm người dùng:

- **Người dùng mới**: Ưu tiên Demographic Filtering (β = 0.8, α = 0.2)
- **Người dùng có ít đánh giá**: Kết hợp CF và DF (α = 0.5, β = 0.5)
- **Người dùng có nhiều đánh giá**: Ưu tiên Collaborative Filtering (α = 0.8, β = 0.2)

#### c) Cascade Hybrid

Lọc dần qua nhiều tầng phương pháp:

1. **Tầng 1**: Sử dụng Demographic Filtering để lọc candidate items
2. **Tầng 2**: Áp dụng Collaborative Filtering để xếp hạng
3. **Tầng 3**: Sử dụng Content-Based để tinh chỉnh kết quả cuối cùng

### 2.4.3. Thuật toán thích ứng trọng số

#### a) Dựa trên số lượng đánh giá

```
if user_rating_count < 5:
    α = 0.1, β = 0.8, γ = 0.1
elif user_rating_count < 20:
    α = 0.4, β = 0.5, γ = 0.1
else:
    α = 0.7, β = 0.2, γ = 0.1
```

#### b) Dựa trên độ tin cậy của dữ liệu

```
α = min(0.8, user_rating_count / 50)
β = 1 - α - γ
γ = 0.1  # Content-based weight
```

#### c) Dựa trên ngữ cảnh sử dụng

```
if context == 'homepage':
    α = 0.5, β = 0.3, γ = 0.2
elif context == 'search':
    α = 0.3, β = 0.2, γ = 0.5
elif context == 'similar_movies':
    α = 0.2, β = 0.1, γ = 0.7
```

### 2.4.4. Xử lý Cold Start trong Hybrid System

#### a) Người dùng mới hoàn toàn

```
recommendation_score = 0.9 × df_score + 0.1 × cb_score
```

#### b) Người dùng có ít đánh giá

```
recommendation_score = 0.3 × cf_score + 0.6 × df_score + 0.1 × cb_score
```

#### c) Người dùng có đánh giá trung bình

```
recommendation_score = 0.6 × cf_score + 0.3 × df_score + 0.1 × cb_score
```

#### d) Người dùng có nhiều đánh giá

```
recommendation_score = 0.8 × cf_score + 0.1 × df_score + 0.1 × cb_score
```

### 2.4.5. Ví dụ minh họa chi tiết

**Kịch bản**: User B có 15 đánh giá, yêu cầu đề xuất phim

**Bước 1: Tính điểm từ từng phương pháp**

- CF Score cho "Inception": 4.2
- DF Score cho "Inception": 3.8
- CB Score cho "Inception": 4.0

**Bước 2: Xác định trọng số**

- User có 15 đánh giá → thuộc nhóm "ít đánh giá"
- α = 0.4, β = 0.5, γ = 0.1

**Bước 3: Tính điểm cuối cùng**

```
Final_Score = 0.4 × 4.2 + 0.5 × 3.8 + 0.1 × 4.0 = 3.98
```

**Kết quả**: "Inception" được đề xuất với điểm 3.98

### 2.4.6. Ưu điểm của Hybrid System

- **Giải quyết Cold Start**: Kết hợp với Demographic Filtering
- **Độ chính xác cao**: Tận dụng ưu điểm của nhiều phương pháp
- **Linh hoạt**: Có thể điều chỉnh trọng số theo ngữ cảnh
- **Robust**: Giảm thiểu nhược điểm của từng phương pháp riêng lẻ
- **Thích ứng**: Tự động điều chỉnh theo hành vi người dùng
- **Đa dạng**: Cung cấp nhiều loại đề xuất khác nhau

## 2.5. ĐÁNH GIÁ HIỆU NĂNG HỆ THỐNG KHUYẾN NGHỊ

### 2.5.1. Các chỉ số đánh giá

#### a) Độ chính xác (Accuracy)

**Mean Absolute Error (MAE):**

```
MAE = (1/n) × ∑|predicted_rating - actual_rating|
```

**Root Mean Square Error (RMSE):**

```
RMSE = √((1/n) × ∑(predicted_rating - actual_rating)²)
```

**Mean Absolute Percentage Error (MAPE):**

```
MAPE = (1/n) × ∑|(actual_rating - predicted_rating) / actual_rating| × 100%
```

#### b) Độ chính xác đề xuất (Recommendation Accuracy)

**Precision@K:**

```
Precision@K = (Number of relevant items in top K) / K
```

**Recall@K:**

```
Recall@K = (Number of relevant items in top K) / (Total relevant items)
```

**F1-Score@K:**

```
F1@K = 2 × (Precision@K × Recall@K) / (Precision@K + Recall@K)
```

#### c) Độ phủ (Coverage)

**Item Coverage:**

```
Item_Coverage = (Number of items can recommend) / (Total items) × 100%
```

**User Coverage:**

```
User_Coverage = (Number of users can get recommendations) / (Total users) × 100%
```

#### d) Đa dạng (Diversity)

**Intra-list Diversity:**

```
Diversity = 1 - (Average_similarity_between_recommended_items)
```

**Inter-list Diversity:**

```
Diversity = 1 - (Average_overlap_between_user_recommendations)
```

#### e) Novelty

**Popularity-based Novelty:**

```
Novelty = Average_popularity_of_recommended_items
```

**Information-based Novelty:**

```
Novelty = -∑(p(i) × log(p(i)))
```

Trong đó p(i) là xác suất item i được đề xuất

### 2.5.2. So sánh hiệu năng các phương pháp

| Phương pháp             | Độ chính xác | Độ phủ     | Đa dạng    | Novelty    | Cold Start | Scalability |
| ----------------------- | ------------ | ---------- | ---------- | ---------- | ---------- | ----------- |
| Collaborative Filtering | Cao          | Thấp       | Trung bình | Thấp       | Không      | Trung bình  |
| Demographic Filtering   | Trung bình   | Cao        | Cao        | Cao        | Có         | Cao         |
| Content-Based           | Trung bình   | Trung bình | Thấp       | Trung bình | Có         | Cao         |
| Hybrid System           | Cao          | Cao        | Cao        | Cao        | Có         | Trung bình  |

### 2.5.3. Đánh giá trải nghiệm người dùng

#### a) User Satisfaction Metrics

- **Click-through Rate (CTR)**: Tỷ lệ người dùng click vào đề xuất
- **Conversion Rate**: Tỷ lệ người dùng thực hiện hành động mong muốn
- **Time on Platform**: Thời gian người dùng sử dụng nền tảng
- **Return Rate**: Tỷ lệ người dùng quay lại sử dụng

#### b) A/B Testing

- So sánh hiệu năng giữa các phương pháp khác nhau
- Đo lường tác động của thay đổi thuật toán
- Tối ưu hóa trọng số trong Hybrid System

## 2.6. CÁC VẤN ĐỀ THỰC TIỄN VÀ GIẢI PHÁP

### 2.6.1. Cold Start Problem

**Vấn đề**: Không thể đề xuất cho người dùng mới hoặc sản phẩm mới do thiếu dữ liệu lịch sử.

**Giải pháp**:

- Sử dụng Demographic Filtering cho người dùng mới
- Yêu cầu người dùng đánh giá nhanh một số sản phẩm mẫu
- Sử dụng Content-Based Filtering cho sản phẩm mới
- Kết hợp thông tin từ các nguồn khác (social media, browsing history)

### 2.6.2. Data Sparsity Problem

**Vấn đề**: Ma trận đánh giá thường rất thưa thớt, ảnh hưởng đến độ chính xác.

**Giải pháp**:

- Sử dụng Matrix Factorization (SVD, ALS)
- Dimensionality Reduction (PCA, t-SNE)
- Imputation techniques (mean, median, collaborative filtering)
- Tăng cường thu thập dữ liệu đánh giá

### 2.6.3. Scalability Problem

**Vấn đề**: Hiệu suất giảm khi số lượng người dùng/sản phẩm tăng.

**Giải pháp**:

- Distributed Computing (Spark, Hadoop)
- Caching strategies (Redis, Memcached)
- Sampling techniques
- Approximate algorithms
- Pre-computation và batch processing

### 2.6.4. Privacy và Security

**Vấn đề**: Bảo vệ thông tin cá nhân người dùng.

**Giải pháp**:

- Differential Privacy
- Federated Learning
- Local Differential Privacy
- Secure Multi-party Computation
- Anonymization techniques

### 2.6.5. Bias và Fairness

**Vấn đề**: Hệ thống có thể tạo ra bias và không công bằng.

**Giải pháp**:

- Fairness-aware algorithms
- Bias detection và mitigation
- Diverse recommendation
- Multi-objective optimization
- Regular auditing và monitoring

## 2.7. KẾT LUẬN CHƯƠNG

Hệ thống khuyến nghị hiện đại cần kết hợp nhiều phương pháp để đạt hiệu quả tối ưu:

1. **Collaborative Filtering** đảm bảo độ chính xác cao cho người dùng có lịch sử đánh giá phong phú
2. **Demographic Filtering** giải quyết vấn đề Cold Start và tăng độ phủ đề xuất
3. **Content-Based Filtering** cung cấp sự đa dạng và khả năng giải thích
4. **Hybrid System** kết hợp ưu điểm của tất cả phương pháp

Việc áp dụng các kỹ thuật tiên tiến như K-Means clustering, vector similarity, adaptive weighting, và đánh giá hiệu năng toàn diện giúp hệ thống ngày càng thông minh và chính xác hơn trong việc đề xuất nội dung phù hợp cho từng người dùng.

Hệ thống MovieMate đã triển khai thành công các phương pháp này, đặc biệt là việc sử dụng vector hóa 30 chiều cho Demographic Filtering và kết hợp linh hoạt với Collaborative Filtering, tạo ra một hệ thống khuyến nghị mạnh mẽ và hiệu quả.
