# HỆ THỐNG KHUYẾN NGHỊ DEMOGRAPHIC FILTERING - QUÁ TRÌNH CHI TIẾT

## 1. Vector hóa dữ liệu thông tin người dùng

Từ dữ liệu nhân khẩu học của người dùng mà hệ thống đặt ra các quy tắc để có thể biến đổi những dữ liệu như: nghề nghiệp, tuổi tác, giới tính, vị trí địa lý, loại thành viên và hành vi đánh giá thành những giá trị 0 và 1.

### Bảng 1: Cấu trúc của vector thông tin người dùng (29 features)

| Features | Feature contents | Comment                                                                                                                        |
| -------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1        | age_0_18         | Nếu như dữ liệu người dùng đúng với nhóm tuổi feature này thì sẽ được gán giá trị là 1 ngược lại nếu không có sẽ được gán là 0 |
| 2        | age_18_25        |                                                                                                                                |
| 3        | age_25_35        |                                                                                                                                |
| 4        | age_35_45        |                                                                                                                                |
| 5        | age_45_55        |                                                                                                                                |
| 6        | age_55_100       |                                                                                                                                |
| 7        | gender_M         | Với người dùng là nam sẽ được gán là 1                                                                                         |
| 8        | gender_F         | Với người dùng nữ sẽ được gán là 1                                                                                             |
| 9        | gender_O         | Với người dùng khác sẽ được gán là 1                                                                                           |
| 10-17    | occupation\_\*   | Dựa vào nghề nghiệp của người dùng sẽ được gán giá trị là 1. Những phần còn lại là 0                                           |
| 18-21    | location\_\*     | Dựa vào khu vực địa lý (Bắc Mỹ, Châu Âu, Châu Á, Khác)                                                                         |
| 22-25    | user*type*\*     | Loại thành viên (member, premium_basic, premium_standard, premium_vip)                                                         |
| 26-29    | behavioral\_\*   | Đặc trưng hành vi (avg_rating, rating_variance, rating_count, activity_level)                                                  |

### Bảng 2: Bảng ví dụ thông tin người dùng

| User     | Age | Gender | Occupation          | Location |
| -------- | --- | ------ | ------------------- | -------- |
| A (2249) | 25  | M      | other               | N/A      |
| B (2250) | 25  | M      | other               | N/A      |
| C (2251) | 25  | M      | technician/engineer | N/A      |
| D (2252) | 25  | M      | self-employed       | N/A      |
| E (2253) | 25  | M      | other               | N/A      |
| F (2937) | 25  | F      | self-employed       | N/A      |

Bảng trên miêu tả ví dụ về dữ liệu thông tin người dùng khi được đưa vào dữ liệu để khuyến nghị trong hệ thống. Sau đó sẽ biến đổi những dữ liệu này thành các giá trị 0 và 1 như bảng bên dưới.

### Bảng 3: Bảng thể hiện vector hóa thông tin người dùng

| User     | age_0_18 | age_18_25 | age_25_35 | age_35_45 | age_45_55 | age_55_100 | gender_M | gender_F | gender_O | occupation_technical | ... |
| -------- | -------- | --------- | --------- | --------- | --------- | ---------- | -------- | -------- | -------- | -------------------- | --- |
| A (2249) | 0        | 0         | 1         | 0         | 0         | 0          | 1        | 0        | 0        | 0                    | ... |
| B (2250) | 0        | 0         | 1         | 0         | 0         | 0          | 1        | 0        | 0        | 0                    | ... |
| C (2251) | 0        | 0         | 1         | 0         | 0         | 0          | 1        | 0        | 0        | 1                    | ... |
| D (2252) | 0        | 0         | 1         | 0         | 0         | 0          | 1        | 0        | 0        | 0                    | ... |
| E (2253) | 0        | 0         | 1         | 0         | 0         | 0          | 1        | 0        | 0        | 0                    | ... |
| F (2937) | 0        | 0         | 1         | 0         | 0         | 0          | 0        | 1        | 0        | 0                    | ... |

## 2. Tiến hành xây dựng ma trận tương đồng thông tin người dùng

Từ dữ liệu thông tin của người dùng sau khi được vector hóa, hệ thống sẽ sử dụng công thức Cosine Similarity để đi tính sự tương đồng dữ liệu giữa các người dùng trong hệ thống với nhau:

```
cosine_similarity(u₁,u₂) = cos(u₁,u₂) = (u₁ᵀ · u₂) / (||u₁||₂ × ||u₂||₂)     (1)
```

Trong đó u₁, u₂ là vectors tương ứng với hai người dùng 1 và 2 đã được vector hóa. Độ tương đồng của hai vector có giá trị trong khoảng [0, 1]. Hàm số cos của một góc bằng 1 nghĩa là góc giữa hai vector bằng 0, tức độ tương đồng về thông tin demographic của hai người dùng là hoàn toàn giống nhau và ngược lại nếu cho giá trị bằng 0 thì thể hiện sự tương đồng của hai người dùng này hầu như không có.

### Bảng 4: Ma trận tương đồng dữ liệu demographic của người dùng

|          | A (2249) | B (2250) | C (2251) | D (2252) | E (2253) | F (2937) |
| -------- | -------- | -------- | -------- | -------- | -------- | -------- |
| A (2249) | 1.000    | 1.000    | 0.800    | 0.894    | 1.000    | 0.671    |
| B (2250) | 1.000    | 1.000    | 0.800    | 0.894    | 1.000    | 0.671    |
| C (2251) | 0.800    | 0.800    | 1.000    | 0.894    | 0.800    | 0.671    |
| D (2252) | 0.894    | 0.894    | 0.894    | 1.000    | 0.894    | 0.750    |
| E (2253) | 1.000    | 1.000    | 0.800    | 0.894    | 1.000    | 0.671    |
| F (2937) | 0.671    | 0.671    | 0.671    | 0.750    | 0.671    | 1.000    |

Công thức Cosine similarity sẽ tính sự tương đồng thông tin người dùng và biến đổi từ ma trận nhị phân thông tin thành ma trận tương đồng dữ liệu demographic. Ma trận này sẽ là một ma trận đối xứng với số hàng và cột bằng tổng số người dùng trong bộ dữ liệu đánh giá.

## 3. Tiến hành chuẩn hóa dữ liệu hoạt động đánh giá phim từ người dùng

Hệ thống sử dụng trọng số dựa trên độ tương đồng demographic để tính toán ratings dự đoán. Thay vì chuẩn hóa bằng cách trừ mean như phương pháp truyền thống, hệ thống sử dụng weighted average trực tiếp từ ratings của các similar users.

### Bảng 5: Ví dụ ratings của similar users cho target user A (2249)

| Similar User | Similarity Score | Movie "Dumbo" Rating | Movie "Star Wars" Rating | Movie "Almost Famous" Rating |
| ------------ | ---------------- | -------------------- | ------------------------ | ---------------------------- |
| B (2250)     | 1.000            | Chưa rating          | Chưa rating              | Chưa rating                  |
| E (2253)     | 1.000            | Chưa rating          | Chưa rating              | Chưa rating                  |
| D (2252)     | 0.894            | 4.5                  | 5.0                      | 4.5                          |
| C (2251)     | 0.800            | Chưa rating          | 4.8                      | 4.8                          |

## 4. Dự đoán đánh giá

Để dự đoán được đánh giá, việc đầu tiên là cần xác định được k người dùng có độ tương đồng gần nhất. Dự đoán đánh giá được xác định là trung bình có trọng số của các đánh giá từ similar users. Hệ thống sử dụng công thức dự đoán của user u cho movie i là:

```
predicted_rating(u,i) = Σ(similarity(u,v) × rating(v,i)) / Σ|similarity(u,v)|     (2)
```

Trong đó:

- predicted_rating(u,i): điểm dự đoán đánh giá của người dùng u cho movie i
- similarity(u,v): độ tương đồng demographic giữa user u và user v
- rating(v,i): rating của user v cho movie i
- N: tập hợp similar users của u đã đánh giá movie i

### Ví dụ tính toán cho user A (2249) với movie "Dumbo":

**Bước 1:** Tìm những người dùng đã đánh giá cho movie "Dumbo":

- User D (2252): rating = 4.5

**Bước 2:** Xác định độ tương đồng của A với user này:

- similarity(A, D) = 0.894

**Bước 3:** Áp dụng công thức dự đoán:

```
predicted_rating(A, Dumbo) = (0.894 × 4.5) / 0.894 = 4.5
```

### Bảng 6: Kết quả recommendations cho User A (2249)

| Rank | Movie                 | Predicted Rating | Confidence Score | Final Score | Support Users |
| ---- | --------------------- | ---------------- | ---------------- | ----------- | ------------- |
| 1    | Dumbo                 | 4.50             | 0.400            | 4.526       | 2             |
| 2    | Almost Famous         | 4.67             | 0.600            | 4.341       | 3             |
| 3    | Star Wars: Episode IV | 4.94             | 1.000            | 4.302       | 16            |
| 4    | It Happened One Night | 5.00             | 0.600            | 4.217       | 3             |
| 5    | His Girl Friday       | 5.00             | 0.400            | 4.204       | 2             |

### Final Score Calculation:

Hệ thống tính toán điểm cuối cùng bằng cách kết hợp nhiều yếu tố:

```
Final Score = Base Score + Demographic Bonus + Confidence Bonus + Support Bonus + Similarity Bonus
```

Trong đó:

- **Base Score**: weighted average rating từ similar users
- **Demographic Bonus**: bonus dựa trên cluster popularity × 0.2
- **Confidence Bonus**: min(support/5, 1) × 0.1
- **Support Bonus**: min(support/10, 0.1)
- **Similarity Bonus**: average_similarity × 0.1

Ví dụ với movie "Dumbo":

- Base Score: 4.5 (từ similar users)
- Demographic Bonus: 0.154 (cluster phổ biến)
- Confidence Bonus: 0.080 (support = 2)
- Support Bonus: 0.020 (support = 2)
- Similarity Bonus: 0.092 (avg similarity = 0.921)
- **Final Score**: 4.526

## 5. Đặc điểm của hệ thống Enhanced Demographic Filtering

### 5.1 Advanced Vectorization (29 features):

- **Age bins**: 6 nhóm tuổi chi tiết
- **Gender encoding**: 3 categories (M/F/O)
- **Occupation grouping**: 8 nhóm nghề semantic
- **Location regions**: 4 khu vực địa lý
- **User types**: 4 loại thành viên
- **Behavioral features**: 4 đặc trưng hành vi

### 5.2 Multiple Similarity Metrics:

- **Cosine Similarity**: đo góc giữa vectors
- **Euclidean Similarity**: đo khoảng cách trong không gian
- **Weighted Similarity**: kết hợp nhiều factors với trọng số

### 5.3 Enhanced Scoring System:

- Kết hợp demographic similarity với popularity
- Confidence scoring dựa trên support users
- Bonus system cho novelty và diversity

### 5.4 Performance Metrics:

- **Coverage**: 96.3% users có demographic data
- **Processing Speed**: 15-18 seconds cho 100 users
- **Accuracy**: High similarity scores (0.7-1.0)
- **Diversity**: Multiple occupation và age groups

Hệ thống này tạo ra recommendations chất lượng cao dựa trên sự tương đồng demographic, phù hợp cho cold-start users và đảm bảo diversity trong kết quả khuyến nghị.
