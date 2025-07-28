# 🧬 Phân tích Vector Thông tin Người dùng (29 Features)

## 📊 **Tổng quan cấu trúc vector**

Vector người dùng có **29 features** được chia thành **6 nhóm chính**:

### **1. Age Features (6 features) - Age bins**

```python
age_bins = [(0, 18), (18, 25), (25, 35), (35, 45), (45, 55), (55, 100)]
```

**Encoding**: One-hot encoding

- `age_0_18`: 1 nếu 0 ≤ tuổi < 18, ngược lại 0
- `age_18_25`: 1 nếu 18 ≤ tuổi < 25, ngược lại 0
- `age_25_35`: 1 nếu 25 ≤ tuổi < 35, ngược lại 0
- `age_35_45`: 1 nếu 35 ≤ tuổi < 45, ngược lại 0
- `age_45_55`: 1 nếu 45 ≤ tuổi < 55, ngược lại 0
- `age_55_100`: 1 nếu 55 ≤ tuổi < 100, ngược lại 0

**Ví dụ**: User 28 tuổi → `[0, 0, 1, 0, 0, 0]`

### **2. Gender Features (3 features)**

```python
gender_options = ['M', 'F', 'O']
```

**Encoding**: One-hot encoding

- `gender_M`: 1 nếu nam, ngược lại 0
- `gender_F`: 1 nếu nữ, ngược lại 0
- `gender_O`: 1 nếu khác, ngược lại 0

**Ví dụ**: User nam → `[1, 0, 0]`

### **3. Occupation Features (8 features) - Nhóm nghề nghiệp**

```python
occupation_groups = {
    'technical': ['engineer', 'programmer', 'scientist', 'technician', 'developer'],
    'creative': ['artist', 'writer', 'designer', 'musician', 'photographer'],
    'business': ['manager', 'executive', 'sales', 'marketing', 'administrator'],
    'education': ['teacher', 'professor', 'academic', 'researcher'],
    'healthcare': ['doctor', 'nurse', 'medical', 'therapist'],
    'service': ['retail', 'hospitality', 'customer service', 'support'],
    'manual': ['construction', 'manufacturing', 'maintenance', 'labor'],
    'other': ['student', 'retired', 'unemployed', 'homemaker', 'other']
}
```

**Encoding**: Multi-label (có thể thuộc nhiều nhóm)

- `occupation_technical`: 1 nếu thuộc nhóm technical
- `occupation_creative`: 1 nếu thuộc nhóm creative
- `occupation_business`: 1 nếu thuộc nhóm business
- `occupation_education`: 1 nếu thuộc nhóm education
- `occupation_healthcare`: 1 nếu thuộc nhóm healthcare
- `occupation_service`: 1 nếu thuộc nhóm service
- `occupation_manual`: 1 nếu thuộc nhóm manual
- `occupation_other`: 1 nếu thuộc nhóm other

**Ví dụ**: User "software engineer" → `[1, 0, 0, 0, 0, 0, 0, 0]`

### **4. Location Features (4 features) - Vùng địa lý**

```python
location_regions = {
    'north_america': ['US', 'CA', 'MX'],
    'europe': ['GB', 'DE', 'FR', 'IT', 'ES'],
    'asia': ['JP', 'KR', 'CN', 'IN', 'TH'],
    'other': []
}
```

**Encoding**: One-hot encoding

- `location_north_america`: 1 nếu thuộc Bắc Mỹ
- `location_europe`: 1 nếu thuộc Châu Âu
- `location_asia`: 1 nếu thuộc Châu Á
- `location_other`: 1 nếu thuộc vùng khác

**⚠️ VẤN ĐỀ**: Không có `southeast_asia` trong vector encoding!

### **5. User Type Features (4 features) - Loại thành viên**

```python
user_types = ['member', 'premium_basic', 'premium_standard', 'premium_vip']
```

**Encoding**: One-hot encoding

- `user_type_member`: 1 nếu là member thường
- `user_type_premium_basic`: 1 nếu là premium basic
- `user_type_premium_standard`: 1 nếu là premium standard
- `user_type_premium_vip`: 1 nếu là premium VIP

**Ví dụ**: User premium standard → `[0, 0, 1, 0]`

### **6. Behavioral Features (4 features) - Hành vi người dùng**

```python
# Tính từ MovieReview của user
behavioral_features = [
    'avg_rating',      # Điểm rating trung bình (normalized 0-1)
    'rating_variance', # Độ biến thiên rating (0-1)
    'rating_count',    # Số lượng rating (normalized, capped tại 100)
    'activity_level'   # Hoạt động gần đây (30 ngày, capped tại 10/ngày)
]
```

**Encoding**: Normalized continuous values (0-1)

- `avg_rating`: (avg_rating - 1) / 4 (scale 1-5 thành 0-1)
- `rating_variance`: min(variance / 2, 1.0)
- `rating_count`: min(count / 100, 1.0)
- `activity_level`: min(recent_ratings / 10, 1.0)

**Ví dụ**: User có avg=4.2, var=0.8, count=50, recent=5 → `[0.8, 0.4, 0.5, 0.5]`

## 🔍 **Giải thích Behavioral Features**

### **Behavioral là gì?**

Behavioral features mô tả **hành vi đánh giá phim** của người dùng, bao gồm:

1. **Average Rating (avg_rating)**:

   - Điểm đánh giá trung bình của user
   - Cao → User dễ tính, thích nhiều phim
   - Thấp → User khó tính, ít khi thích phim

2. **Rating Variance (rating_variance)**:

   - Độ biến thiên trong cách đánh giá
   - Cao → User có sự khác biệt lớn trong đánh giá (1 sao cho phim dở, 5 sao cho phim hay)
   - Thấp → User đánh giá ổn định (luôn cho khoảng 3-4 sao)

3. **Rating Count (rating_count)**:

   - Số lượng phim đã đánh giá
   - Cao → User tích cực, có nhiều dữ liệu
   - Thấp → User mới hoặc ít tương tác

4. **Activity Level (activity_level)**:
   - Mức độ hoạt động gần đây (30 ngày)
   - Cao → User đang tích cực sử dụng
   - Thấp → User ít hoạt động hoặc inactive

### **Tại sao Behavioral quan trọng?**

- Giúp phân biệt user có cùng demographic nhưng khác hành vi
- Cải thiện độ chính xác recommendation
- Phản ánh sở thích và pattern sử dụng thực tế

## ⚠️ **VẤNĐỀ NGHIÊM TRỌNG: Location Encoding Mismatch**

### **1. Vector Encoding hiện tại (4 regions)**:

```python
location_regions = {
    'north_america': ['US', 'CA', 'MX'],      # Index 0
    'europe': ['GB', 'DE', 'FR', 'IT', 'ES'], # Index 1
    'asia': ['JP', 'KR', 'CN', 'IN', 'TH'],   # Index 2
    'other': []                               # Index 3
}
```

### **2. Location Detection trả về**:

- **Việt Nam users**: Được detect thành `vietnam` hoặc `việt nam`
- **Thái Lan users**: Được detect thành `thailand`
- **Singapore users**: Được detect thành `singapore`

### **3. Kết quả encoding sai**:

- ❌ **Việt Nam**: Không match với ['US', 'CA', 'MX', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'KR', 'CN', 'IN', 'TH'] → `location_other = 1`
- ❌ **Thái Lan**: Match với 'TH' → `location_asia = 1` (Đúng nhưng không chính xác, TH thuộc Southeast Asia)
- ❌ **Singapore**: Không match → `location_other = 1`

### **4. Hậu quả**:

- Tất cả Vietnamese users bị classify thành 'other'
- Mất thông tin geographic quan trọng
- Giảm độ chính xác recommendation
- Không nhất quán với location detection system

## 🔧 **Giải pháp cần thực hiện**

### **Option 1: Cập nhật Vector Encoding (Khuyến nghị)**

```python
# Cập nhật location_regions trong AdvancedDemographicVectorizer
location_regions = {
    'north_america': ['US', 'CA', 'MX'],
    'europe': ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI'],
    'asia': ['JP', 'KR', 'CN', 'IN'],
    'southeast_asia': ['VN', 'SG', 'MY', 'ID', 'PH', 'TH', 'TW', 'HK'],
    'other': []
}
```

**Vector sẽ thành 30 features** (thêm 1 feature cho southeast_asia)

### **Option 2: Cập nhật Location Detection**

```python
# Sửa LocationDetectionView để luôn trả về English format phù hợp với encoding
# "Thành phố Hồ Chí Minh, Việt Nam" → "Ho Chi Minh City, Vietnam"
# Đảm bảo detect logic match với encoding logic
```

### **Option 3: Hybrid Approach**

- Cập nhật cả vector encoding và detection
- Thêm multilingual support
- Đảm bảo consistency giữa detection và encoding

## 📈 **Tóm tắt Vector Structure**

| **Feature Group** | **Count** | **Encoding Type** | **Purpose**          |
| ----------------- | --------- | ----------------- | -------------------- |
| Age Bins          | 6         | One-hot           | Phân nhóm tuổi       |
| Gender            | 3         | One-hot           | Giới tính            |
| Occupation Groups | 8         | Multi-label       | Nhóm nghề nghiệp     |
| Location Regions  | 4         | One-hot           | Vùng địa lý          |
| User Types        | 4         | One-hot           | Loại thành viên      |
| Behavioral        | 4         | Normalized        | Hành vi đánh giá     |
| **TOTAL**         | **29**    | Mixed             | **Complete profile** |

## 🎯 **Ưu điểm của cấu trúc hiện tại**

1. **Comprehensive**: Cover toàn bộ thông tin demographic và behavioral
2. **Scalable**: Dễ thêm features mới
3. **Balanced**: Mỗi nhóm có weight hợp lý
4. **Interpretable**: Dễ hiểu ý nghĩa từng feature
5. **ML-ready**: Format chuẩn cho machine learning

## ⚡ **Điểm cần cải thiện**

1. **Location encoding mismatch** (CRITICAL)
2. **Behavioral features** có thể thêm genre preferences
3. **Temporal features** (thời gian tham gia, seasonal patterns)
4. **Social features** (friends, social interactions)
5. **Content features** (favorite genres, actors, directors)

## 📋 **Kết luận**

Vector 29 chiều được thiết kế rất tốt và comprehensive. Tuy nhiên, **vấn đề location encoding mismatch** cần được sửa ngay lập tức để đảm bảo tính chính xác của hệ thống recommendation, đặc biệt đối với users từ Việt Nam và Đông Nam Á.
