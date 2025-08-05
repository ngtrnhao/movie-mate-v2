# BÁO CÁO PHÂN TÍCH K-MEANS CLUSTERING

## Hệ thống Gợi ý Phim Movie Mate v2

---

## 📊 TỔNG QUAN KẾT QUẢ

### **Thống kê cơ bản:**

- **Tổng số users:** 6,337
- **Users có demographics:** 6,096 (96.2%)
- **Users trong K-means clusters:** 6,096 (100% coverage)
- **Số K-means clusters:** 7 clusters

### **Chất lượng Clustering:**

- **Silhouette Score:** 0.174
- **Calinski-Harabasz Score:** 483.8
- **Đánh giá:** ❌ Chất lượng thấp (Silhouette < 0.3)

---

## 🎯 PHÂN TÍCH CHI TIẾT CÁC CLUSTERS

### **Cluster kmeans_0 - Nam Trung Niên (45-56 tuổi)**

- **Số users:** 989 (16.2%)
- **Tuổi:** 45-56 (TB: 49.9 ± 4.4)
- **Giới tính:** 100% Nam
- **Nghề nghiệp phổ biến:**
  - Executive/Managerial: 157 users
  - Academic/Educator: 125 users
  - Technician/Engineer: 106 users

### **Cluster kmeans_1 - Nam Trưởng Thành (21-43 tuổi)**

- **Số users:** 858 (14.1%)
- **Tuổi:** 21-43 (TB: 35.0 ± 0.7)
- **Giới tính:** 100% Nam
- **Nghề nghiệp phổ biến:**
  - Executive/Managerial: 177 users
  - Technician/Engineer: 116 users
  - Other: 92 users

### **Cluster kmeans_2 - Nam Trẻ (25 tuổi)**

- **Số users:** 1,540 (25.3%) - **Lớn nhất**
- **Tuổi:** 25 (TB: 25.0 ± 0.0)
- **Giới tính:** 100% Nam
- **Nghề nghiệp phổ biến:**
  - Other: 206 users
  - Executive/Managerial: 192 users
  - Technician/Engineer: 180 users

### **Cluster kmeans_3 - Sinh Viên (18-21 tuổi)**

- **Số users:** 1,069 (17.5%)
- **Tuổi:** 18-21 (TB: 18.0 ± 0.1)
- **Giới tính:** 75.4% Nam, 24.6% Nữ
- **Nghề nghiệp phổ biến:**
  - College/Grad Student: 534 users
  - Other: 106 users
  - Programmer: 59 users

### **Cluster kmeans_5 - Nữ Đa Lứa Tuổi (18-56 tuổi)**

- **Số users:** 1,369 (22.5%)
- **Tuổi:** 18-56 (TB: 35.0 ± 10.9)
- **Giới tính:** 100% Nữ
- **Nghề nghiệp phổ biến:**
  - Academic/Educator: 207 users
  - Other: 191 users
  - Executive/Managerial: 138 users

### **Cluster kmeans_6 - Đa Dạng (13-102 tuổi)**

- **Số users:** 49 (0.8%) - **Nhỏ nhất**
- **Tuổi:** 13-102 (TB: 31.2 ± 19.5)
- **Giới tính:** 55.1% Nam, 42.9% Nữ, 2.0% Khác
- **Nghề nghiệp phổ biến:**
  - K-12 Student: 9 users
  - Technician/Engineer: 5 users
  - Scientist: 4 users

### **Cluster kmeans_7 - Trẻ Em (1 tuổi)**

- **Số users:** 222 (3.6%)
- **Tuổi:** 1 (TB: 1.0 ± 0.0)
- **Giới tính:** 64.9% Nam, 35.1% Nữ
- **Nghề nghiệp phổ biến:**
  - K-12 Student: 163 users
  - Other: 27 users
  - Unemployed: 12 users

---

## 🧪 KẾT QUẢ TEST CÁC TRƯỜNG HỢP PHÂN CỤM

### **Vấn đề phát hiện:**

Tất cả các test cases đều được gán vào **cluster kmeans_6** (cluster đa dạng), điều này cho thấy:

1. **Thuật toán gán cluster có vấn đề** - không phân biệt được các demographics khác nhau
2. **Cluster kmeans_6 hoạt động như "catch-all"** - nhận tất cả users không phù hợp với clusters khác
3. **Chất lượng clustering thấp** - không thể phân biệt rõ ràng các nhóm demographics

### **Test Cases cụ thể:**

#### **Test Case 1: Nam trẻ (18-24) - Sinh viên**

- **Được gán:** kmeans_6
- **Lý do không phù hợp:**
  - Tuổi chênh lệch: 9.2 năm
  - Nghề nghiệp không khớp (sinh viên vs K-12 student)

#### **Test Case 2: Nữ trung niên (35-44) - Quản lý**

- **Được gán:** kmeans_6
- **Lý do không phù hợp:**
  - Giới tính không khớp (Nữ vs Nam chủ đạo)
  - Nghề nghiệp không khớp (executive vs K-12 student)

#### **Test Case 3: Nam cao tuổi (56+) - Đã nghỉ hưu**

- **Được gán:** kmeans_6
- **Lý do không phù hợp:**
  - Tuổi chênh lệch lớn: 33.8 năm
  - Nghề nghiệp không khớp (retired vs K-12 student)

---

## ⚠️ VẤN ĐỀ PHÁT HIỆN

### **1. Chất lượng Clustering Thấp**

- **Silhouette Score:** 0.174 (< 0.3 - ngưỡng chấp nhận được)
- **Nguyên nhân:** Thuật toán không phân biệt tốt giữa các nhóm demographics

### **2. Vấn đề Gán Cluster**

- **Fallback cluster:** kmeans_6 nhận tất cả users không phù hợp
- **Không phân biệt được:** Tuổi, giới tính, nghề nghiệp khác nhau
- **Thuật toán similarity:** Có thể có vấn đề trong tính toán

### **3. Phân bố Clusters Không Cân Bằng**

- **Cluster lớn nhất:** kmeans_2 (25.3%) - Nam 25 tuổi
- **Cluster nhỏ nhất:** kmeans_6 (0.8%) - Đa dạng
- **Thiếu clusters:** Cho các nhóm demographics cụ thể

### **4. Dữ liệu Có Vấn Đề**

- **Tuổi 1 tuổi:** 222 users (có thể là dữ liệu lỗi)
- **Tuổi 25 cố định:** 1,540 users (có thể là dữ liệu mẫu)
- **Thiếu đa dạng:** Trong một số clusters

---

## 🔧 KHUYẾN NGHỊ CẢI THIỆN

### **1. Cải thiện Thuật toán Clustering**

```python
# Tăng số clusters
n_clusters = 12-15  # Thay vì 7

# Sử dụng thuật toán khác
from sklearn.cluster import DBSCAN, AgglomerativeClustering
# Hoặc ensemble methods
```

### **2. Cải thiện Feature Engineering**

```python
# Thêm features mới
- Genre preferences
- Rating patterns
- Watch history
- Time-based features
```

### **3. Cải thiện Gán Cluster**

```python
# Sử dụng multiple similarity metrics
- Cosine similarity
- Euclidean distance
- Weighted combination
```

### **4. Làm sạch Dữ liệu**

```python
# Loại bỏ dữ liệu không hợp lệ
- Tuổi < 13 hoặc > 100
- Dữ liệu trùng lặp
- Dữ liệu thiếu thông tin
```

### **5. Cải thiện Vector Representation**

```python
# Tối ưu hóa vector features
- Normalize features
- Feature selection
- Dimensionality reduction
```

---

## 📈 KẾ HOẠCH HÀNH ĐỘNG

### **Giai đoạn 1: Khắc phục ngay (1-2 tuần)**

1. **Làm sạch dữ liệu** - loại bỏ users có tuổi không hợp lệ
2. **Tăng số clusters** - từ 7 lên 12-15 clusters
3. **Cải thiện thuật toán gán cluster** - sử dụng multiple similarity metrics

### **Giai đoạn 2: Cải thiện trung hạn (2-4 tuần)**

1. **Thêm features mới** - behavioral patterns, genre preferences
2. **Tối ưu hóa vector representation** - feature selection, normalization
3. **Test với thuật toán khác** - DBSCAN, Agglomerative clustering

### **Giai đoạn 3: Tối ưu hóa dài hạn (1-2 tháng)**

1. **Implement ensemble methods** - kết hợp nhiều thuật toán
2. **Real-time clustering** - cập nhật clusters theo thời gian thực
3. **A/B testing** - so sánh hiệu quả các phương pháp

---

## 🎯 MỤC TIÊU CHẤT LƯỢNG

### **Target Metrics:**

- **Silhouette Score:** > 0.4 (từ 0.174 hiện tại)
- **Calinski-Harabasz Score:** > 1000 (từ 483.8 hiện tại)
- **Cluster balance:** Mỗi cluster 5-20% users
- **Accuracy:** > 80% users được gán đúng cluster

### **Success Criteria:**

- Users trong cùng cluster có demographics tương tự
- Không có cluster "catch-all"
- Phân biệt rõ ràng các nhóm tuổi, giới tính, nghề nghiệp
- Coverage > 95% users

---

## 📋 KẾT LUẬN

K-means clustering hiện tại **hoạt động nhưng chất lượng thấp**. Hệ thống cần được cải thiện đáng kể để:

1. **Phân biệt tốt hơn** giữa các nhóm demographics
2. **Gán cluster chính xác** cho từng user
3. **Cân bằng phân bố** users trong các clusters
4. **Tăng chất lượng** recommendations dựa trên demographics

**Ưu tiên cao nhất:** Làm sạch dữ liệu và cải thiện thuật toán gán cluster để khắc phục vấn đề "catch-all cluster".

---

_Báo cáo được tạo ngày: 02/08/2025_
_Dựa trên phân tích 6,096 users với demographics_
