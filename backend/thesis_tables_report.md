# 📊 BÁO CÁO DỮ LIỆU CHI TIẾT CÁC BẢNG TRONG LUẬN VĂN

**Ngày tạo báo cáo:** 2025-08-02T19:32:45.295139

## 📋 BẢNG 2.1: MA TRẬN UTILITY MATRIX

### Thông tin người dùng

| **User ID** | **Username** | **Điểm trung bình** |
|-------------|--------------|---------------------|
| 1085 | ml_user_548 | 3.13 |
| 2285 | ml_user_1748 | 2.71 |
| 1384 | ml_user_847 | 3.37 |
| 2457 | ml_user_1920 | 2.74 |
| 1534 | ml_user_997 | 3.09 |

### Thông tin phim

| **Movie ID** | **Tên phim** | **Điểm trung bình** |
|--------------|--------------|---------------------|
| 282646 | American Beauty | 4.29 |
| 58129 | Star Wars: Episode V - The Empire Strikes Back | 4.27 |
| 55535 | Star Wars: Episode IV - A New Hope | 4.41 |
| 75090 | Jurassic Park | 3.74 |
| 72565 | Terminator 2: Judgment Day | 4.03 |

### Ma trận đánh giá

| **User** | **American Beauty...** | **Star Wars: Epis...** | **Star Wars: Epis...** | **Jurassic Park...** | **Terminator 2: J...** |
|----------|------------------|------------------|------------------|------------------|------------------|
| ml_user_548 | 5.0 | 4.5 | 4.0 | 2.0 | 4.0 |
| ml_user_1748 | 3.0 | 4.0 | 4.0 | 4.0 | 3.0 |
| ml_user_847 | 5.0 | 4.0 | 3.5 | 3.5 | 3.0 |
| ml_user_1920 | 5.0 | 5.0 | 5.0 | 4.0 | 3.0 |
| ml_user_997 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |

## 📋 BẢNG 2.2: CHUẨN HÓA ĐÁNH GIÁ

| **User** | **Phim** | **Điểm gốc** | **Điểm TB User** | **Điểm chuẩn hóa** |
|----------|----------|--------------|------------------|-------------------|
| ml_user_2031 | The Silence of the L... | 5.0 | 3.81 | +1.19 |
| ml_user_2031 | The Next Karate Kid... | 3.0 | 3.81 | -0.81 |
| ml_user_2031 | Mrs. Doubtfire... | 3.0 | 3.81 | -0.81 |
| ml_user_2031 | Menace II Society... | 3.0 | 3.81 | -0.81 |
| ml_user_2031 | The Firm... | 4.0 | 3.81 | +0.19 |
| ml_user_2031 | Dazed and Confused... | 4.0 | 3.81 | +0.19 |
| ml_user_2031 | A Bronx Tale... | 4.0 | 3.81 | +0.19 |
| ml_user_2031 | Speed... | 3.0 | 3.81 | -0.81 |
| ml_user_2031 | The Lion King... | 4.0 | 3.81 | +0.19 |
| ml_user_2031 | Forrest Gump... | 4.0 | 3.81 | +0.19 |

## 📋 BẢNG 2.3: MA TRẬN TƯƠNG ĐỒNG NGƯỜI DÙNG

### Thông tin người dùng

| **User ID** | **Username** | **Tuổi** | **Giới tính** | **Nghề nghiệp** |
|-------------|--------------|----------|---------------|-----------------|
| 2249 | ml_user_1712 | 25 | M | other |
| 2250 | ml_user_1713 | 25 | M | other |
| 2251 | ml_user_1714 | 25 | M | technician/engineer |
| 2252 | ml_user_1715 | 25 | M | self-employed |
| 2253 | ml_user_1716 | 25 | M | other |

### Ma trận tương đồng

| **User** | **ml_user_1712** | **ml_user_1713** | **ml_user_1714** | **ml_user_1715** | **ml_user_1716** |
|----------|----------------|----------------|----------------|----------------|----------------|
| ml_user_1712 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ml_user_1713 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ml_user_1714 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ml_user_1715 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| ml_user_1716 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## 📋 BẢNG 2.4: VECTOR HÓA NHÂN KHẨU HỌC

### Thông tin người dùng

| **User ID** | **Username** | **Tuổi** | **Giới tính** | **Nghề nghiệp** | **Location** |
|-------------|--------------|----------|---------------|-----------------|-------------|
| 2249 | ml_user_1712 | 25 | M | other | N/A |
| 2250 | ml_user_1713 | 25 | M | other | N/A |
| 2251 | ml_user_1714 | 25 | M | technician/engineer | N/A |
| 2252 | ml_user_1715 | 25 | M | self-employed | N/A |
| 2253 | ml_user_1716 | 25 | M | other | N/A |

### Vector tuổi (Age Vector)

| **User** | **[0-18]** | **[18-25]** | **[25-35]** | **[35-45]** | **[45-55]** | **[55+]** |
|----------|------------|------------|------------|------------|------------|---------|
| ml_user_1712 | 0 | 1 | 0 | 0 | 0 | 0 |
| ml_user_1713 | 0 | 1 | 0 | 0 | 0 | 0 |
| ml_user_1714 | 0 | 1 | 0 | 0 | 0 | 0 |
| ml_user_1715 | 0 | 1 | 0 | 0 | 0 | 0 |
| ml_user_1716 | 0 | 1 | 0 | 0 | 0 | 0 |

### Vector giới tính (Gender Vector)

| **User** | **[M]** | **[F]** | **[O]** |
|----------|---------|---------|---------|
| ml_user_1712 | 1 | 0 | 0 |
| ml_user_1713 | 1 | 0 | 0 |
| ml_user_1714 | 1 | 0 | 0 |
| ml_user_1715 | 1 | 0 | 0 |
| ml_user_1716 | 1 | 0 | 0 |

### Vector nghề nghiệp (Occupation Vector)

| **User** | **[Tech]** | **[Creative]** | **[Business]** | **[Education]** | **[Healthcare]** | **[Service]** | **[Manual]** | **[Other]** |
|----------|------------|---------------|---------------|----------------|----------------|-------------|-------------|------------|
| ml_user_1712 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| ml_user_1713 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| ml_user_1714 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ml_user_1715 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ml_user_1716 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

### Vector địa lý (Location Vector)

| **User** | **[NA]** | **[EU]** | **[ASIA]** | **[SEA]** | **[OTHER]** |
|----------|----------|----------|-----------|-----------|-----------|
| ml_user_1712 | 0 | 0 | 0 | 0 | 0 |
| ml_user_1713 | 0 | 0 | 0 | 0 | 0 |
| ml_user_1714 | 0 | 0 | 0 | 0 | 0 |
| ml_user_1715 | 0 | 0 | 0 | 0 | 0 |
| ml_user_1716 | 0 | 0 | 0 | 0 | 0 |

## 📋 BẢNG 2.5: DỮ LIỆU CLUSTERING

**Tổng số clusters:** 0

## 📋 BẢNG 2.6: VÍ DỤ KHUYẾN NGHỊ

### Ví dụ 1: User ml_user_2403

**Loại khuyến nghị:** hybrid
**Thời gian tạo:** 2025-07-29T13:36:29.299133+00:00

*Không có dữ liệu khuyến nghị*

### Ví dụ 2: User ml_user_2403

**Loại khuyến nghị:** hybrid
**Thời gian tạo:** 2025-07-29T13:36:29.381519+00:00

*Không có dữ liệu khuyến nghị*

### Ví dụ 3: User ynhinguyen

**Loại khuyến nghị:** hybrid
**Thời gian tạo:** 2025-07-27T19:26:24.522032+00:00

*Không có dữ liệu khuyến nghị*

## 🎯 KẾT LUẬN

Dữ liệu trên cho thấy:

- **Utility Matrix**: Ma trận đánh giá user-item với độ thưa thớt cao
- **Rating Normalization**: Chuẩn hóa đánh giá để loại bỏ bias cá nhân
- **User Similarity**: Tính toán tương đồng dựa trên đặc điểm nhân khẩu học
- **Demographic Vectorization**: Chuyển đổi thông tin nhân khẩu thành vector số
- **Clustering**: Nhóm người dùng theo đặc điểm tương đồng
- **Recommendations**: Ví dụ thực tế về khuyến nghị được tạo ra

Các bảng này minh họa rõ ràng quy trình xử lý dữ liệu và thuật toán khuyến nghị trong hệ thống Movie Mate.