# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT

## 2.1. TỔNG QUAN VỀ HỆ THỐNG KHUYẾN NGHỊ

### 2.1.1. Định nghĩa và khái niệm

Hệ thống khuyến nghị (Recommendation System) là một hệ thống thông minh được thiết kế để dự đoán và đề xuất các sản phẩm, dịch vụ hoặc nội dung phù hợp với sở thích và nhu cầu của người dùng. Trong bối cảnh nền tảng xem phim trực tuyến, hệ thống này đóng vai trò quan trọng trong việc:

- **Cá nhân hóa trải nghiệm**: Đề xuất phim phù hợp với sở thích cá nhân
- **Tăng cường tương tác**: Khuyến khích người dùng khám phá nội dung mới
- **Giải quyết vấn đề thông tin quá tải**: Lọc và sắp xếp nội dung từ kho dữ liệu khổng lồ
- **Tối ưu hóa doanh thu**: Tăng tỷ lệ xem phim và thời gian sử dụng

### 2.1.2. Phân loại các phương pháp khuyến nghị

Hệ thống khuyến nghị được phân thành ba nhóm chính:

1. **Content-Based Filtering**: Dựa trên đặc tính của sản phẩm và lịch sử tương tác
2. **Collaborative Filtering**: Dựa trên hành vi và đánh giá của cộng đồng người dùng
3. **Hybrid Approaches**: Kết hợp nhiều phương pháp để tối ưu hóa kết quả

## 2.2. COLLABORATIVE FILTERING (CF)

### 2.2.1. Nguyên lý hoạt động

Collaborative Filtering là phương pháp khuyến nghị dựa trên nguyên tắc "những người dùng có sở thích tương tự sẽ thích những sản phẩm tương tự". Phương pháp này không cần phân tích nội dung của sản phẩm mà chỉ dựa vào:

- **Lịch sử đánh giá** của người dùng
- **Mức độ tương đồng** giữa các người dùng
- **Patterns** trong hành vi đánh giá

### 2.2.2. Kỹ thuật K-Nearest Neighbors (KNN)

#### 2.2.2.1. Nguyên lý cơ bản

KNN là kỹ thuật phổ biến nhất trong Collaborative Filtering, hoạt động theo các bước:

1. **Tính toán độ tương đồng** giữa người dùng mục tiêu và tất cả người dùng khác
2. **Chọn K người dùng** có độ tương đồng cao nhất (K-nearest neighbors)
3. **Dự đoán đánh giá** dựa trên đánh giá trung bình của K người dùng này
4. **Đề xuất sản phẩm** có điểm dự đoán cao nhất

#### 2.2.2.2. Công thức tính độ tương đồng

**Cosine Similarity:**

```
sim(u,v) = (∑(r_ui × r_vi)) / (√(∑r_ui²) × √(∑r_vi²))
```

**Pearson Correlation:**

```
sim(u,v) = (∑(r_ui - r̄_u)(r_vi - r̄_v)) / (√(∑(r_ui - r̄_u)²) × √(∑(r_vi - r̄_v)²))
```

Trong đó:

- `r_ui`: Đánh giá của user u cho item i
- `r̄_u`: Đánh giá trung bình của user u
- `r_vi`: Đánh giá của user v cho item i
- `r̄_v`: Đánh giá trung bình của user v

#### 2.2.2.3. Công thức dự đoán

```
pred(u,i) = r̄_u + (∑(sim(u,v) × (r_vi - r̄_v))) / (∑|sim(u,v)|)
```

### 2.2.3. Ví dụ minh họa

**Kịch bản**: Hệ thống có 4 người dùng (A, B, C, D) và 3 bộ phim (Fight Club, Doraemon, Inception)

| User | Fight Club | Doraemon | Inception |
| ---- | ---------- | -------- | --------- |
| A    | 5          | ?        | 4         |
| B    | 5          | 5        | 3         |
| C    | 2          | 1        | 5         |
| D    | 4          | 4        | 4         |

**Phân tích**:

- User A và B có sở thích tương tự (đều thích Fight Club)
- User B đã đánh giá Doraemon 5 điểm
- Dự đoán: User A cũng sẽ thích Doraemon

**Kết quả**: Hệ thống đề xuất Doraemon cho User A với điểm dự đoán cao

### 2.2.4. Ưu điểm và nhược điểm

**Ưu điểm:**

- Không cần phân tích nội dung sản phẩm
- Có thể phát hiện sở thích ẩn
- Hiệu quả với dữ liệu đánh giá phong phú
- Dễ hiểu và triển khai

**Nhược điểm:**

- **Cold Start Problem**: Không thể đề xuất cho người dùng mới
- **Sparsity Problem**: Ma trận đánh giá thường thưa thớt
- **Scalability**: Tính toán phức tạp khi số lượng người dùng lớn
- **Privacy Concerns**: Cần chia sẻ dữ liệu đánh giá

## 2.3. DEMOGRAPHIC FILTERING

### 2.3.1. Nguyên lý hoạt động

Demographic Filtering là phương pháp khuyến nghị dựa trên đặc điểm nhân khẩu học của người dùng. Phương pháp này giải quyết vấn đề Cold Start bằng cách:

- **Phân tích thông tin cá nhân**: Tuổi, giới tính, nghề nghiệp, địa điểm
- **Nhóm người dùng tương tự**: Dựa trên đặc điểm nhân khẩu học
- **Đề xuất dựa trên nhóm**: Sử dụng hành vi của nhóm để dự đoán

### 2.3.2. Kỹ thuật phân cụm nhân khẩu học

#### 2.3.2.1. Vector hóa thông tin người dùng

Hệ thống chuyển đổi thông tin nhân khẩu học thành vector số:

```
User Vector = [Age_Bins, Gender, Occupation, Location, User_Type, Behavioral_Features]
```

**Chi tiết các thành phần:**

1. **Age Bins (6 features)**: Phân nhóm tuổi thành 6 khoảng

   - 18-25: [1,0,0,0,0,0]
   - 26-35: [0,1,0,0,0,0]
   - 36-45: [0,0,1,0,0,0]
   - 46-55: [0,0,0,1,0,0]
   - 56-65: [0,0,0,0,1,0]
   - 65+: [0,0,0,0,0,1]

2. **Gender (3 features)**: Mã hóa giới tính

   - Male: [1,0,0]
   - Female: [0,1,0]
   - Other: [0,0,1]

3. **Occupation (8 features)**: Phân loại nghề nghiệp

   - Student, Business, Technical, Creative, Service, etc.

4. **Location (4 features)**: Phân vùng địa lý

   - Urban, Suburban, Rural, International

5. **User Type (4 features)**: Loại tài khoản

   - Member, Premium Basic, Premium Pro, Admin

6. **Behavioral Features (4 features)**: Đặc điểm hành vi
   - Average Rating, Rating Variance, Rating Count, Activity Level

#### 2.3.2.2. K-Means Clustering

**Nguyên lý:**

- Nhóm người dùng có vector tương tự vào cùng cluster
- Mỗi cluster đại diện cho một nhóm nhân khẩu học
- Sử dụng thuật toán K-Means để tối ưu hóa phân cụm

**Công thức tính khoảng cách:**

```
distance(u,c) = √(∑(u_i - c_i)²)
```

**Quá trình phân cụm:**

1. Khởi tạo K centroids ngẫu nhiên
2. Gán mỗi user vào centroid gần nhất
3. Cập nhật centroids dựa trên trung bình của cluster
4. Lặp lại cho đến khi hội tụ

#### 2.3.2.3. Rule-Based Clustering (Fallback)

Khi K-Means không khả dụng, hệ thống sử dụng quy tắc đơn giản:

```
IF age BETWEEN 18-25 AND gender = 'M' THEN cluster = 'Young_Male'
IF age BETWEEN 18-25 AND gender = 'F' THEN cluster = 'Young_Female'
IF age BETWEEN 26-35 AND occupation = 'student' THEN cluster = 'Young_Professional'
...
```

### 2.3.3. Thuật toán đề xuất

#### 2.3.3.1. Tìm người dùng tương tự

```
similar_users = find_users_in_same_cluster(target_user)
```

#### 2.3.3.2. Tính điểm đề xuất

```
recommendation_score = average_rating(similar_users, movie) × similarity_weight
```

#### 2.3.3.3. Xử lý Cold Start

**Cho người dùng mới (không có đánh giá):**

1. Tìm cluster phù hợp dựa trên vector nhân khẩu học
2. Lấy đánh giá từ người dùng trong cluster
3. Đề xuất phim có điểm cao nhất

**Cho người dùng có đánh giá:**

1. Kết hợp thông tin nhân khẩu học và lịch sử đánh giá
2. Tìm người dùng tương tự trong cluster
3. Tính điểm dự đoán dựa trên đánh giá của họ

### 2.3.4. Ví dụ minh họa

**Kịch bản**: User A (25 tuổi, Nam, Sinh viên) mới đăng ký

**Bước 1: Vector hóa**

```
User_A_Vector = [1,0,0,0,0,0, 1,0,0, 1,0,0,0,0,0,0,0, 1,0,0,0, 1,0,0,0, 0,0,0,0]
```

**Bước 2: Phân cụm**

- Tìm cluster phù hợp nhất (ví dụ: Cluster_1)
- Cluster_1 chứa 150 người dùng tương tự

**Bước 3: Đề xuất**

- Lấy top 10 phim được đánh giá cao nhất trong Cluster_1
- Đề xuất cho User A

**Kết quả**: User A nhận được danh sách phim phù hợp với nhóm nhân khẩu học

### 2.3.5. Ưu điểm và nhược điểm

**Ưu điểm:**

- **Giải quyết Cold Start**: Có thể đề xuất cho người dùng mới
- **Không cần lịch sử đánh giá**: Dựa trên thông tin cá nhân
- **Dễ hiểu**: Logic rõ ràng, minh bạch
- **Bảo mật**: Không chia sẻ dữ liệu đánh giá cá nhân

**Nhược điểm:**

- **Độ chính xác thấp**: So với Collaborative Filtering
- **Stereotyping**: Có thể tạo ra định kiến
- **Thiếu tính cá nhân hóa**: Chỉ dựa trên nhóm
- **Phụ thuộc vào dữ liệu nhân khẩu học**: Cần thông tin đầy đủ

## 2.4. HYBRID RECOMMENDATION SYSTEM

### 2.4.1. Nguyên lý kết hợp

Hệ thống Hybrid kết hợp nhiều phương pháp để tối ưu hóa kết quả:

```
Final_Score = α × CF_Score + β × DF_Score + γ × CB_Score
```

Trong đó:

- `α, β, γ`: Trọng số của từng phương pháp
- `CF_Score`: Điểm từ Collaborative Filtering
- `DF_Score`: Điểm từ Demographic Filtering
- `CB_Score`: Điểm từ Content-Based Filtering

### 2.4.2. Chiến lược kết hợp

#### 2.4.2.1. Weighted Hybrid

```
recommendation_score = 0.4 × cf_score + 0.4 × df_score + 0.2 × cb_score
```

#### 2.4.2.2. Switching Hybrid

- **Người dùng mới**: Ưu tiên Demographic Filtering
- **Người dùng có ít đánh giá**: Kết hợp CF và DF
- **Người dùng có nhiều đánh giá**: Ưu tiên Collaborative Filtering

#### 2.4.2.3. Cascade Hybrid

1. Sử dụng Demographic Filtering để lọc candidate items
2. Áp dụng Collaborative Filtering để xếp hạng
3. Sử dụng Content-Based để tinh chỉnh kết quả

### 2.4.3. Ưu điểm của Hybrid System

- **Giải quyết Cold Start**: Kết hợp với Demographic Filtering
- **Độ chính xác cao**: Tận dụng ưu điểm của nhiều phương pháp
- **Linh hoạt**: Có thể điều chỉnh trọng số theo ngữ cảnh
- **Robust**: Giảm thiểu nhược điểm của từng phương pháp riêng lẻ

## 2.5. ĐÁNH GIÁ HIỆU NĂNG

### 2.5.1. Các chỉ số đánh giá

#### 2.5.1.1. Độ chính xác (Accuracy)

**Mean Absolute Error (MAE):**

```
MAE = (1/n) × ∑|predicted_rating - actual_rating|
```

**Root Mean Square Error (RMSE):**

```
RMSE = √((1/n) × ∑(predicted_rating - actual_rating)²)
```

#### 2.5.1.2. Độ phủ (Coverage)

```
Coverage = (Number_of_items_can_recommend / Total_items) × 100%
```

#### 2.5.1.3. Đa dạng (Diversity)

```
Diversity = 1 - (Average_similarity_between_recommended_items)
```

#### 2.5.1.4. Novelty

```
Novelty = Average_popularity_of_recommended_items
```

### 2.5.2. So sánh hiệu năng

| Phương pháp             | Độ chính xác | Độ phủ | Đa dạng    | Novelty | Cold Start |
| ----------------------- | ------------ | ------ | ---------- | ------- | ---------- |
| Collaborative Filtering | Cao          | Thấp   | Trung bình | Thấp    | Không      |
| Demographic Filtering   | Trung bình   | Cao    | Cao        | Cao     | Có         |
| Hybrid System           | Cao          | Cao    | Cao        | Cao     | Có         |

## 2.6. KẾT LUẬN CHƯƠNG

Hệ thống khuyến nghị phim hiện đại cần kết hợp nhiều phương pháp để đạt hiệu quả tối ưu:

1. **Collaborative Filtering** đảm bảo độ chính xác cao cho người dùng có lịch sử
2. **Demographic Filtering** giải quyết vấn đề Cold Start và tăng độ phủ
3. **Hybrid System** kết hợp ưu điểm của cả hai phương pháp

Việc áp dụng các kỹ thuật tiên tiến như K-Means clustering, vector similarity, và adaptive weighting giúp hệ thống ngày càng thông minh và chính xác hơn trong việc đề xuất nội dung phù hợp cho từng người dùng.
